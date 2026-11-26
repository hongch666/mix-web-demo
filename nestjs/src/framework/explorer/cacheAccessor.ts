/** 缓存写入选项，缺省沿用缓存服务的全局 TTL */
export interface CacheWriteOptions {
  /** L1 本地缓存有效期（秒） */
  localTtl?: number;
  /** L2 Redis 缓存有效期（秒） */
  redisTtl?: number;
}

/** 缓存读写抽象，供缓存注解执行器使用而不依赖具体缓存服务 */
export interface CacheAccessor {
  /** 读取缓存，未命中返回 undefined */
  get<T>(key: string): Promise<T | undefined>;
  /** 写入缓存，可按选项覆盖两级 TTL */
  set<T>(key: string, value: T, options?: CacheWriteOptions): Promise<void>;
  /** 批量失效缓存 key */
  deleteMany(keys: string[]): Promise<void>;
}

/** 缓存读写抽象的注入令牌，由缓存模块提供实现 */
export const CACHE_ACCESSOR = Symbol("CACHE_ACCESSOR");
