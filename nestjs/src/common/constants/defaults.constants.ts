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

  // ===== RabbitMQ 日志攒批配置 =====
  /** 批量大小：达到此数量立即 flush */
  static readonly LOG_BATCH_SIZE = 100;
  /** flush 间隔（毫秒）：超过此时间未 flush 则自动触发 */
  static readonly LOG_BATCH_FLUSH_INTERVAL_MS = 1000;
  /** 缓冲区最大容量：超过后强制 flush 防止 OOM */
  static readonly LOG_BATCH_MAX_BUFFER_SIZE = 5000;
}
