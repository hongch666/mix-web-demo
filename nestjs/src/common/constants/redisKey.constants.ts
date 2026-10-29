/**
 * Redis 标识常量 — 锁Key、客户端Token、OAuth状态Key、Lua脚本
 */
export class RedisKeys {
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
}
