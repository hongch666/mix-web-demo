import { Injectable, OnModuleDestroy, OnModuleInit } from "@nestjs/common";
import Redis from "ioredis";
import { Defaults, Messages, RedisKeys } from "src/common/constants";
import { LoggerService } from "src/module/common/logger/logger.service";
import { RedisService } from "src/module/common/redis/redis.service";

/** 多级缓存的写入选项，缺省沿用 Defaults 中的全局 TTL */
export interface CacheWriteOptions {
  /** L1 本地缓存有效期（秒） */
  localTtl?: number;
  /** L2 Redis 缓存有效期（秒） */
  redisTtl?: number;
}

/** L1 本地缓存条目，createdAt 与 expiresAt 均为毫秒级时间戳 */
interface LocalCacheEntry {
  value: unknown;
  createdAt: number;
  expiresAt: number;
}

/** Redis 中的缓存载荷，用对象包一层保证 null 结果也能与未命中区分 */
interface CachePayload {
  value: unknown;
}

/**
 * 多级缓存服务，提供 L1 本地内存加 L2 Redis 的读写与失效能力
 * L1 按条目的写入时间做过期与容量淘汰，L2 统一加前缀并带 TTL；Redis 未配置时退化为纯本地缓存
 * 失效时通过 Redis Pub/Sub 广播被删除的 key，其它实例据此清理自己的 L1，避免多实例读到过期本地值
 */
@Injectable()
export class CacheService implements OnModuleInit, OnModuleDestroy {
  private readonly local = new Map<string, LocalCacheEntry>();
  private readonly localTtl: number = Defaults.CACHE_LOCAL_TTL_SECONDS;
  private readonly redisTtl: number = Defaults.CACHE_REDIS_TTL_SECONDS;
  private readonly localMaxEntries: number = Defaults.CACHE_LOCAL_MAX_ENTRIES;
  private subscriber: Redis | null = null;

  constructor(
    private readonly redisService: RedisService,
    private readonly logger: LoggerService,
  ) {}

  /**
   * 模块初始化时订阅跨实例失效频道，未配置 Redis 时跳过
   */
  onModuleInit(): void {
    this.subscribeInvalidationChannel();
  }

  /**
   * 模块销毁时清空本地缓存并释放订阅连接
   */
  async onModuleDestroy(): Promise<void> {
    this.local.clear();

    const subscriber: Redis | null = this.subscriber;
    this.subscriber = null;
    if (!subscriber) {
      return;
    }

    try {
      await subscriber.quit();
    } catch (error) {
      this.logger.error(
        Messages.CACHE_INVALIDATE_UNSUBSCRIBE_FAILED(String(error)),
      );
    }
  }

  /**
   * 读取缓存，先查 L1 本地再查 L2 Redis，均未命中返回 undefined
   * 缓存值为 null 时返回 null，用于区分「缓存了空结果」与「未命中」
   */
  async get<T>(key: string): Promise<T | undefined> {
    const localEntry: LocalCacheEntry | undefined = this.local.get(key);
    if (localEntry) {
      if (localEntry.expiresAt > Date.now()) {
        const ageSeconds: number = (Date.now() - localEntry.createdAt) / 1000;
        this.logger.debug(Messages.CACHE_L1_HIT(key, ageSeconds));
        return localEntry.value as T;
      }
      this.local.delete(key);
    }

    const redis = this.redisService.getClient();
    if (!redis) {
      this.logger.debug(Messages.CACHE_MISS(key));
      return undefined;
    }

    try {
      const raw: string | null = await redis.get(this.buildRedisKey(key));
      if (raw === null) {
        this.logger.debug(Messages.CACHE_MISS(key));
        return undefined;
      }
      const payload: CachePayload = JSON.parse(raw) as CachePayload;
      this.logger.debug(Messages.CACHE_L2_HIT(key));
      this.writeLocal(key, payload.value);
      return payload.value as T;
    } catch (error) {
      this.logger.error(Messages.CACHE_L2_READ_FAILED(key, String(error)));
      return undefined;
    }
  }

  /**
   * 写入两级缓存，L1 写入本地并设置过期时间，L2 写入 Redis 并设置 TTL
   * Redis 写入失败只记录日志，不影响业务返回
   */
  async set<T>(
    key: string,
    value: T,
    options: CacheWriteOptions = {},
  ): Promise<void> {
    const redisTtl: number = options.redisTtl ?? this.redisTtl;
    this.writeLocal(key, value, options.localTtl);

    const redis = this.redisService.getClient();
    if (!redis) {
      return;
    }

    try {
      const payload: CachePayload = { value };
      await redis.set(
        this.buildRedisKey(key),
        JSON.stringify(payload),
        "EX",
        redisTtl,
      );
      this.logger.debug(Messages.CACHE_WRITTEN(key, redisTtl));
    } catch (error) {
      this.logger.error(Messages.CACHE_L2_WRITE_FAILED(key, String(error)));
    }
  }

  /**
   * 失效单个 key 的两级缓存
   */
  async delete(key: string): Promise<void> {
    await this.deleteMany([key]);
  }

  /**
   * 批量失效多个 key 的两级缓存：本地立即删除，Redis 删除与跨实例广播并行执行
   */
  async deleteMany(keys: string[]): Promise<void> {
    if (keys.length === 0) {
      return;
    }

    keys.forEach((key: string): void => {
      this.local.delete(key);
      this.logger.debug(Messages.CACHE_EVICTED(key));
    });

    const redis = this.redisService.getClient();
    if (!redis) {
      return;
    }

    await Promise.all([
      this.publishInvalidation(redis, keys),
      this.deleteRedisKeys(redis, keys),
    ]);
  }

  /**
   * 订阅跨实例缓存失效频道，收到通知后清理本地对应条目
   * 订阅连接必须是独立的 duplicate 客户端，主客户端处于订阅模式后无法再执行读写命令
   */
  private subscribeInvalidationChannel(): void {
    const redis = this.redisService.getClient();
    if (!redis || typeof redis.duplicate !== "function") {
      return;
    }

    try {
      const subscriber: Redis = redis.duplicate();
      subscriber.on("message", (channel: string, message: string): void => {
        if (channel === RedisKeys.CACHE_INVALIDATE_CHANNEL) {
          this.clearLocalByMessage(message);
        }
      });
      subscriber
        .subscribe(RedisKeys.CACHE_INVALIDATE_CHANNEL)
        .catch((error: unknown): void => {
          this.logger.error(
            Messages.CACHE_INVALIDATE_SUBSCRIBE_FAILED(String(error)),
          );
        });
      this.subscriber = subscriber;
    } catch (error) {
      this.logger.error(
        Messages.CACHE_INVALIDATE_SUBSCRIBE_FAILED(String(error)),
      );
    }
  }

  /**
   * 解析失效通知并清理本地缓存，通知丢失时由 L1 TTL 兜底
   */
  private clearLocalByMessage(message: string): void {
    try {
      const keys: string[] = JSON.parse(message) as string[];
      keys.forEach((key: string): boolean => this.local.delete(key));
      this.logger.debug(Messages.CACHE_L1_INVALIDATED(keys.length));
    } catch (error) {
      this.logger.error(
        Messages.CACHE_INVALIDATE_MESSAGE_FAILED(String(error)),
      );
    }
  }

  /**
   * 向失效频道广播被删除的 key，失败只记录日志
   */
  private async publishInvalidation(
    redis: Redis,
    keys: string[],
  ): Promise<void> {
    try {
      await redis.publish(
        RedisKeys.CACHE_INVALIDATE_CHANNEL,
        JSON.stringify(keys),
      );
    } catch (error) {
      this.logger.error(
        Messages.CACHE_PUBLISH_FAILED(keys.join(","), String(error)),
      );
    }
  }

  /**
   * 删除 Redis 中对应的缓存 key，失败只记录日志
   */
  private async deleteRedisKeys(redis: Redis, keys: string[]): Promise<void> {
    try {
      const redisKeys: string[] = keys.map((key: string): string =>
        this.buildRedisKey(key),
      );
      await redis.del(...redisKeys);
    } catch (error) {
      this.logger.error(
        Messages.CACHE_L2_DELETE_FAILED(keys.join(","), String(error)),
      );
    }
  }

  /**
   * 拼接 Redis 中的完整缓存 key，业务 key 只提供主体部分
   */
  private buildRedisKey(key: string): string {
    return `${Defaults.CACHE_KEY_PREFIX}${key}`;
  }

  /**
   * 写入 L1 本地缓存，超过容量上限时淘汰最早写入的条目
   */
  private writeLocal(key: string, value: unknown, ttlSeconds?: number): void {
    if (!this.local.has(key) && this.local.size >= this.localMaxEntries) {
      const oldestKey: string | undefined = this.local.keys().next().value;
      if (oldestKey !== undefined) {
        this.local.delete(oldestKey);
      }
    }

    const ttl: number = ttlSeconds ?? this.localTtl;
    const createdAt: number = Date.now();
    this.local.set(key, {
      value,
      createdAt,
      expiresAt: createdAt + ttl * 1000,
    });
  }
}
