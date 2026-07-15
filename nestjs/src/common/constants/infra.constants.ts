/**
 * 基础设施标识常量 — 锁Key、队列名、客户端Token、Lua脚本
 */
export class InfraKeys {
  // ===== Redis 客户端 Token =====
  static readonly REDIS_CLIENT = "REDIS_CLIENT";

  // ===== 分布式锁 Key =====
  static readonly LOCK_TASK_API_LOG_CLEANUP = "lock:task:api:log:cleanup";
  static readonly LOCK_TASK_ARTICLE_LOG_CLEANUP =
    "lock:task:article:log:cleanup";

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
