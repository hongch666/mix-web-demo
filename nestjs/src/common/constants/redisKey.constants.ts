/**
 * Redis 标识常量 — 锁Key、客户端Token、OAuth状态Key、Lua脚本
 */
export class RedisKeys {
  // ===== Redis 客户端 Token =====
  static readonly REDIS_CLIENT = "REDIS_CLIENT";

  // ===== 分布式锁 Key =====
  static readonly LOCK_TASK_API_LOG_CLEANUP = "lock:task:api:log:cleanup";
  static readonly LOCK_TASK_ARTICLE_LOG_CLEANUP =
    "lock:task:article:log:cleanup";

  // ===== OAuth 状态 Key =====
  static readonly OAUTH_GITHUB_STATE = (state: string): string =>
    `oauth:github:state:${state}`;

  // ===== Lua 脚本 =====
  /** 解锁脚本: 仅锁持有者可释放 */
  static readonly UNLOCK_SCRIPT = `
    if redis.call("get", KEYS[1]) == ARGV[1] then
      return redis.call("del", KEYS[1])
    else
      return 0
    end
  `;
}
