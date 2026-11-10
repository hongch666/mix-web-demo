/**
 * Redis 标识常量 — 锁Key、客户端Token、OAuth状态Key、Lua脚本
 */
export class RedisKeys {
  // ===== 多级缓存 Key =====

  /** 构造用户单个页面表格列设置的缓存 key 主体，实际 key 由 CacheService 统一加前缀 */
  static readonly CACHE_TABLE_SETTINGS = (
    userId: number,
    tableKey: string,
  ): string => `table:settings:${userId}:${tableKey}`;

  /** 构造用户全部页面表格列设置的缓存 key 主体，保存与删除列设置时一并失效 */
  static readonly CACHE_TABLE_SETTINGS_LIST = (userId: number): string =>
    `table:settings:${userId}:all`;

  /** 构造文章日志用户名映射的缓存 key 主体，userId 升序拼接保证同一批用户命中同一 key */
  static readonly CACHE_ARTICLE_LOG_USER_NAMES = (userIds: number[]): string =>
    `article:log:user:${[...userIds].sort((a: number, b: number): number => a - b).join(",")}`;

  /** 构造文章日志文章标题映射的缓存 key 主体，articleId 升序拼接保证同一批文章命中同一 key */
  static readonly CACHE_ARTICLE_LOG_ARTICLE_TITLES = (
    articleIds: number[],
  ): string =>
    `article:log:article:${[...articleIds].sort((a: number, b: number): number => a - b).join(",")}`;

  // ===== GitHub OAuth =====

  // ===== OAuth 状态 Key =====

  /** GitHub 授权 state 的缓存 key 模板 */
  static readonly OAUTH_GITHUB_STATE = (state: string): string =>
    `oauth:github:state:${state}`;

  // ===== Redis 客户端与锁 =====

  // ===== Redis 客户端 Token =====

  /** Redis 客户端的注入令牌 */
  static readonly REDIS_CLIENT = "REDIS_CLIENT";

  // ===== 分布式锁 Key =====

  /** API 日志清理任务的分布式锁 key */
  static readonly LOCK_TASK_API_LOG_CLEANUP = "lock:task:api:log:cleanup";

  // ===== Lua 脚本 =====

  /** 解锁脚本: 仅锁持有者可释放 */
  /** 比对持有者后再删除锁的 Lua 脚本 */
  static readonly UNLOCK_SCRIPT = `
    if redis.call("get", KEYS[1]) == ARGV[1] then
      return redis.call("del", KEYS[1])
    else
      return 0
    end
  `;

  // ===== 多级缓存通道 =====

  /** 多级缓存跨实例失效的 Pub/Sub 频道，按服务隔离避免与 FastAPI 的失效消息格式互相干扰，写操作删除 Redis 缓存后向该频道广播被失效的 key */
  static readonly CACHE_INVALIDATE_CHANNEL = "cache:invalidate:nestjs";
}
