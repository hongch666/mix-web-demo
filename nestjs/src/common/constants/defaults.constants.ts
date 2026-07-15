/**
 * 配置默认值常量 — 数字、URL、超时等非消息型默认值
 */
export class Defaults {
  // ===== 启动 =====
  static readonly INIT_IP = "127.0.0.1";

  // ===== OSS =====
  static readonly OSS_HTTP_PUT_METHOD = "PUT";
  static readonly OSS_DEFAULT_CONTENT_TYPE = "application/octet-stream";

  // ===== Redis 分布式锁过期时间 =====
  static readonly LOCK_TASK_API_LOG_CLEANUP_EXPIRE = 3600;
  static readonly LOCK_TASK_ARTICLE_LOG_CLEANUP_EXPIRE = 3600;
}
