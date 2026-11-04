import { SetMetadata } from "@nestjs/common";

/** @Cacheable 的元数据键 */
export const CACHEABLE_KEY = "cacheable";

/** @CacheEvict 的元数据键 */
export const CACHE_EVICT_KEY = "cache_evict";

/** 缓存 key 的生成方式：固定字符串或按方法入参生成，返回空串表示本次跳过缓存 */
export type CacheKey<TArgs extends unknown[]> =
  | string
  | ((...args: TArgs) => string);

/** @Cacheable 装饰器的配置项 */
export interface CacheableOptions<TArgs extends unknown[] = unknown[]> {
  /** 缓存 key，无入参方法可直接传固定字符串 */
  key: CacheKey<TArgs>;
  /** L1 本地缓存有效期（秒），缺省沿用全局配置 */
  localTtl?: number;
  /** L2 Redis 缓存有效期（秒），缺省沿用全局配置 */
  redisTtl?: number;
  /** 是否缓存 null 结果，缺省不缓存 */
  cacheNull?: boolean;
}

/** @CacheEvict 装饰器的配置项 */
export interface CacheEvictOptions<TArgs extends unknown[] = unknown[]> {
  /** 需要失效的缓存 key，可传单个或多个 */
  keys: CacheKey<TArgs> | CacheKey<TArgs>[];
}

/**
 * 查询缓存注解，只写入元数据，两级缓存的读写由 CacheExplorer 在启动期织入
 * @example
 * @Cacheable({ key: (userId: number) => RedisKeys.CACHE_TABLE_SETTINGS_LIST(userId) })
 */
export const Cacheable = <TArgs extends unknown[] = unknown[]>(
  options: CacheableOptions<TArgs>,
): MethodDecorator => SetMetadata(CACHEABLE_KEY, options);

/**
 * 缓存失效注解，只写入元数据，原方法成功执行后由 CacheExplorer 删除对应 key
 * @example
 * @CacheEvict<[number, string]>({ keys: [(userId: number) => RedisKeys.CACHE_TABLE_SETTINGS_LIST(userId)] })
 */
export const CacheEvict = <TArgs extends unknown[] = unknown[]>(
  options: CacheEvictOptions<TArgs>,
): MethodDecorator => SetMetadata(CACHE_EVICT_KEY, options);
