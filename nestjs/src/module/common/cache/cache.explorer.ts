import { Injectable, OnModuleDestroy, OnModuleInit } from "@nestjs/common";
import { DiscoveryService, MetadataScanner, Reflector } from "@nestjs/core";
import { Messages } from "src/common/constants";
import {
  CACHE_EVICT_KEY,
  CACHEABLE_KEY,
  CacheEvictOptions,
  CacheableOptions,
  CacheKey,
} from "src/framework/decorators/cache.decorator";
import { LoggerService } from "src/module/common/logger/logger.service";
import { CacheService, CacheWriteOptions } from "./cache.service";

/** 可被织入缓存逻辑的异步方法签名 */
type CacheableMethod = (...args: unknown[]) => Promise<unknown>;

/**
 * 按注解配置生成缓存 key，字符串直接返回，函数按方法入参求值，空串表示本次跳过缓存
 */
function resolveCacheKey(key: CacheKey<unknown[]>, args: unknown[]): string {
  return typeof key === "string" ? key : key(...args);
}

/**
 * 缓存注解执行器，应用启动时扫描全部 Provider，为带 @Cacheable / @CacheEvict 的方法织入缓存读写
 * Nest 的拦截器只覆盖 HTTP 链路，Service 方法的横切由该执行器在启动期包装，注解本身只保存元数据
 */
@Injectable()
export class CacheExplorer implements OnModuleInit, OnModuleDestroy {
  // 同一 key 正在进行中的回源任务，避免并发未命中时重复打库
  private readonly inFlight = new Map<string, Promise<unknown>>();

  constructor(
    private readonly discoveryService: DiscoveryService,
    private readonly metadataScanner: MetadataScanner,
    private readonly reflector: Reflector,
    private readonly cacheService: CacheService,
    private readonly logger: LoggerService,
  ) {}

  /**
   * 遍历全部 Provider 的原型方法，命中缓存注解时用包装后的方法替换实例方法
   */
  onModuleInit(): void {
    this.discoveryService.getProviders().forEach((wrapper): void => {
      const instance = wrapper.instance as Record<string, unknown> | null;
      if (!instance || typeof instance !== "object") {
        return;
      }

      const prototype = Object.getPrototypeOf(instance) as Record<
        string,
        unknown
      > | null;
      if (!prototype) {
        return;
      }

      this.metadataScanner
        .getAllMethodNames(prototype)
        .forEach((methodName: string): void => {
          this.wrapMethod(instance, prototype, methodName);
        });
    });
  }

  /**
   * 模块销毁时清空回源任务表，避免残留 Promise 引用
   */
  onModuleDestroy(): void {
    this.inFlight.clear();
  }

  /**
   * 按注解元数据包装单个方法，已经是实例自有属性的方法不重复织入
   */
  private wrapMethod(
    instance: Record<string, unknown>,
    prototype: Record<string, unknown>,
    methodName: string,
  ): void {
    const methodRef = prototype[methodName];
    if (typeof methodRef !== "function") {
      return;
    }
    if (Object.prototype.hasOwnProperty.call(instance, methodName)) {
      return;
    }

    const cacheable: CacheableOptions | undefined = this.reflector.get<
      CacheableOptions | undefined
    >(CACHEABLE_KEY, methodRef);
    const evict: CacheEvictOptions | undefined = this.reflector.get<
      CacheEvictOptions | undefined
    >(CACHE_EVICT_KEY, methodRef);
    if (!cacheable && !evict) {
      return;
    }

    const original: CacheableMethod = (methodRef as CacheableMethod).bind(
      instance,
    );
    if (cacheable) {
      instance[methodName] = this.buildCacheable(original, cacheable);
      return;
    }
    if (evict) {
      instance[methodName] = this.buildEvict(original, evict);
    }
  }

  /**
   * 构造查询缓存包装方法：先查两级缓存，未命中时同一 key 的并发请求复用同一次回源
   */
  private buildCacheable(
    original: CacheableMethod,
    options: CacheableOptions,
  ): CacheableMethod {
    return async (...args: unknown[]): Promise<unknown> => {
      const key: string = resolveCacheKey(options.key, args);
      if (!key) {
        return original(...args);
      }

      const cached: unknown = await this.readCache(key);
      if (cached !== undefined) {
        return cached;
      }

      const pending: Promise<unknown> | undefined = this.inFlight.get(key);
      if (pending) {
        return pending;
      }

      const task: Promise<unknown> = this.loadAndFill(
        key,
        original,
        args,
        options,
      );
      this.inFlight.set(key, task);
      try {
        return await task;
      } finally {
        this.inFlight.delete(key);
      }
    };
  }

  /**
   * 执行原方法并在成功后回填缓存，回源失败时直接抛出且不写缓存
   */
  private async loadAndFill(
    key: string,
    original: CacheableMethod,
    args: unknown[],
    options: CacheableOptions,
  ): Promise<unknown> {
    const result: unknown = await original(...args);
    if (result !== undefined && (result !== null || options.cacheNull)) {
      await this.writeCache(key, result, {
        localTtl: options.localTtl,
        redisTtl: options.redisTtl,
      });
    }
    return result;
  }

  /**
   * 构造缓存失效包装方法，原方法成功返回后删除注解声明的全部 key，抛错时不删除
   */
  private buildEvict(
    original: CacheableMethod,
    options: CacheEvictOptions,
  ): CacheableMethod {
    const keys: CacheKey<unknown[]>[] = Array.isArray(options.keys)
      ? options.keys
      : [options.keys];

    return async (...args: unknown[]): Promise<unknown> => {
      const result: unknown = await original(...args);
      const cacheKeys: string[] = keys
        .map((key: CacheKey<unknown[]>): string => resolveCacheKey(key, args))
        .filter((key: string): boolean => key.length > 0);
      await this.evictCache(cacheKeys);
      return result;
    };
  }

  /**
   * 读取缓存，异常时降级为未命中并记录日志
   */
  private async readCache(key: string): Promise<unknown> {
    try {
      return await this.cacheService.get<unknown>(key);
    } catch (error) {
      this.logger.warning(
        Messages.CACHE_EXPLORER_READ_FAILED(key, String(error)),
      );
      return undefined;
    }
  }

  /**
   * 写入缓存，异常时放弃本次回填并记录日志，不影响业务返回
   */
  private async writeCache(
    key: string,
    value: unknown,
    options: CacheWriteOptions,
  ): Promise<void> {
    try {
      await this.cacheService.set(key, value, options);
    } catch (error) {
      this.logger.warning(
        Messages.CACHE_EXPLORER_WRITE_FAILED(key, String(error)),
      );
    }
  }

  /**
   * 失效缓存，异常时记录日志，不把缓存故障抛给业务调用方
   */
  private async evictCache(keys: string[]): Promise<void> {
    if (keys.length === 0) {
      return;
    }

    try {
      await this.cacheService.deleteMany(keys);
    } catch (error) {
      this.logger.warning(
        Messages.CACHE_EXPLORER_EVICT_FAILED(keys.join(","), String(error)),
      );
    }
  }
}
