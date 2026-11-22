/**
 * 配置默认值常量 — 数字、URL、超时等非消息型默认值
 */
export class Defaults {
  // ===== OSS =====

  /** OSS 上传使用的 HTTP 方法 */
  static readonly OSS_HTTP_PUT_METHOD = "PUT";
  /** OSS 上传文件的默认 Content-Type */
  static readonly OSS_DEFAULT_CONTENT_TYPE = "application/octet-stream";

  // ===== Redis 分布式锁过期时间 =====

  /** API 日志清理任务的分布式锁过期秒数 */
  static readonly LOCK_TASK_API_LOG_CLEANUP_EXPIRE = 3600;

  /** OSS 对象清理任务的分布式锁过期秒数 */
  static readonly LOCK_TASK_OSS_CLEANUP_EXPIRE = 1800;

  /** OSS 对象清理宽限期（毫秒）：创建未满 1h 的对象不清理，给业务建立引用的时间 */
  static readonly OSS_CLEANUP_GRACE_MS = 60 * 60 * 1000;

  /** OSS 对象清理单次列取每批数量 */
  static readonly OSS_LIST_PAGE_SIZE = 1000;

  /** multipart 单文件体积上限默认值（MB），可由配置 files.max_size 覆盖 */
  static readonly MAX_UPLOAD_SIZE_MB = 5;

  /** OSS 清理允许操作的 key 前缀白名单，避免误删配置或其它业务对象 */
  static readonly OSS_CLEANUP_KEY_PREFIXES = [
    "pic/",
    "pdf/",
    "excel/",
    "articles/",
  ] as const;

  // ===== 链路追踪 =====

  /** 手动创建 span 时使用的 tracer 名称：定时任务等无请求入口的场景 */
  static readonly OTEL_TRACER_NAME = "nestjs";

  // ===== 日志保留期限 =====

  /** 日志保留月数：API 日志与文章日志超过该期限后由定时任务分批清理，数仓按同一保留期清理已过期日志 */
  static readonly LOG_RETENTION_MONTHS = 3;

  // ===== RabbitMQ 队列 =====

  /** API 日志生产者与消费者共用的队列名 */
  static readonly RABBITMQ_API_LOG_QUEUE = "api-log-queue";

  /** 文章日志生产者与消费者共用的队列名 */
  static readonly RABBITMQ_ARTICLE_LOG_QUEUE = "article-log-queue";

  // ===== RabbitMQ 日志攒批配置 =====

  /** 批量大小：达到此数量立即 flush */
  static readonly LOG_BATCH_SIZE = 100;
  /** flush 间隔（毫秒）：超过此时间未 flush 则自动触发 */
  static readonly LOG_BATCH_FLUSH_INTERVAL_MS = 1000;
  /** 缓冲区最大容量：超过后强制 flush 防止 OOM */
  static readonly LOG_BATCH_MAX_BUFFER_SIZE = 5000;
  /** 日志清理单批删除上限：分批执行 deleteMany，避免一次性删除整月数据造成数据库压力尖峰 */
  static readonly LOG_CLEANUP_BATCH_SIZE = 5000;

  // ===== 日志删除墓碑 =====

  /** 删除墓碑的保留秒数（90 天）：数仓同步后墓碑即可回收，超出该窗口仍未被同步的删除会由数仓保留期清理兜底 */
  static readonly LOG_DELETION_TTL_SECONDS = 7776000;

  /** 删除墓碑单页返回上限：供数仓按游标拉取，与日志同步接口的单页上限保持一致 */
  static readonly LOG_DELETION_SYNC_MAX_LIMIT = 5000;

  // ===== 远程调用服务名 =====

  /** Nacos 中 Spring 服务的注册名 */
  static readonly SPRING_SERVICE_NAME = "spring";

  /** Nacos 中 FastAPI 服务的注册名 */
  static readonly FASTAPI_SERVICE_NAME = "fastapi";

  // ===== 远程调用连接池 =====

  /** 内网服务调用的最大并发连接数 */
  static readonly REMOTE_CALL_MAX_SOCKETS = 50;

  /** GitHub 外部接口单次请求超时时间（毫秒） */
  static readonly GITHUB_HTTP_TIMEOUT_MS = 10000;

  // ===== 多级缓存 =====

  /** 多级缓存在 Redis 中的 key 统一前缀，隔离业务 key 与锁、OAuth 状态等其它 Redis 用法 */
  static readonly CACHE_KEY_PREFIX = "cache:";

  /** L1 本地缓存有效期（秒，5 分钟），跨实例的本地值最多滞后该时长，与 Spring/FastAPI 侧 L1 TTL 对齐 */
  static readonly CACHE_LOCAL_TTL_SECONDS = 300;

  /** L2 Redis 缓存有效期（秒），需与 FastAPI 侧 L2_CACHE_TTL 对齐 */
  static readonly CACHE_REDIS_TTL_SECONDS = 86400;

  /** L1 本地缓存最大条目数，超出后淘汰最早写入的条目 */
  static readonly CACHE_LOCAL_MAX_ENTRIES = 1000;

  /** 文章日志名称映射的 L1 本地缓存有效期（秒），只用于单实例内合并并发翻页，不追求跨实例实时 */
  static readonly ARTICLE_LOG_MAPPING_LOCAL_TTL_SECONDS = 10;

  /** 文章日志名称映射的 L2 Redis 缓存有效期（秒），5 分钟内复用一次远程批量查询结果 */
  static readonly ARTICLE_LOG_MAPPING_REDIS_TTL_SECONDS = 300;
}
