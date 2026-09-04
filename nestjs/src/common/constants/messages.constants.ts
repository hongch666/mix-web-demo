/**
 * 消息常量类
 */
export class Messages {
  static readonly INTERNAL_TOKEN_SERVICE_NAME_MISMATCH = (
    requiredServiceName: string,
    actualServiceName: string,
  ): string =>
    `${this.SERVICE_NAME_MISMATCH}. 期望: ${requiredServiceName}, 获得: ${actualServiceName}`;

  static readonly INTERNAL_TOKEN_VERIFICATION_SUCCESS = (
    userId: number,
    serviceName: string,
  ): string => `内部令牌验证成功 - 用户ID: ${userId}, 服务: ${serviceName}`;

  static readonly INTERNAL_TOKEN_VERIFICATION_FAILED = (
    message: string,
  ): string => `令牌验证失败: ${message}`;

  static readonly STARTUP_SERVICE_ADDRESS = (
    ip: string,
    port: number,
  ): string => `服务地址: http://${ip}:${port}`;

  static readonly STARTUP_SWAGGER_ADDRESS = (
    ip: string,
    port: number,
  ): string => `Swagger文档地址: http://${ip}:${port}/api-docs`;

  static readonly ARTICLE_LOG_SPRING_MESSAGE = (message: string): string =>
    `接收到 Spring 发送的 ArticleLog 消息: ${message}`;

  static readonly ARTICLE_LOG_MESSAGE = (message: string): string =>
    `接收到 ArticleLog 消息: ${message}`;

  static readonly ARTICLE_LOG_PROCESS_FAILED = (message: string): string =>
    `处理 ArticleLog 消息失败: ${message}`;

  static readonly ARTICLE_LOG_MISSING_ACTION = (message: string): string =>
    `ArticleLog 消息缺少 action 字段: ${message}`;

  static readonly ARTICLE_LOG_MISSING_CONTENT = (message: string): string =>
    `ArticleLog 消息缺少 content 字段: ${message}`;

  static readonly ARTICLE_LOG_INVALID_ACTION = (action: string): string =>
    `无效的操作类型: ${action}`;

  static readonly ARTICLE_LOG_INVALID_ACTION_DETAIL = (
    action: string,
  ): string => `ArticleLog 消息包含无效的 action 值: ${action}`;

  static readonly ARTICLE_LOG_PREPARE_SAVE = (message: string): string =>
    `准备保存 ArticleLog: ${message}`;

  static readonly API_LOG_SPRING_MESSAGE = (message: string): string =>
    `接收到 Spring 发送的 ApiLog 消息: ${message}`;

  static readonly API_LOG_MESSAGE = (message: string): string =>
    `接收到 ApiLog 消息: ${message}`;

  static readonly API_LOG_IGNORED_MESSAGE = (message: string): string =>
    `收到非 API 日志格式的消息，已忽略: ${message}`;

  static readonly API_LOG_RESPONSE_TIME_CORRECTED = (
    responseTime: number,
  ): string => `接口响应时间为${responseTime}，已将其设置为0: `;

  static readonly API_LOG_PROCESS_FAILED = (message: string): string =>
    `处理 ApiLog 消息失败: ${message}`;

  static readonly API_LOG_INDEX_CREATED = (indexName: string): string =>
    `ApiLog 索引已创建: ${indexName}`;

  static readonly ARTICLE_LOG_INDEX_CREATED = (indexName: string): string =>
    `索引已创建: ${indexName}`;

  static readonly EXCEPTION_LOG = (
    method: string,
    url: string,
    errorIdentifier: string,
    message: string,
    stack: string | undefined,
  ): string =>
    `[${method}] ${url} - [${errorIdentifier}] ${message} - ${stack}`;

  static readonly API_LOG_REQUEST = (
    userId: number,
    username: string,
    sessionId: string,
    method: string,
    url: string,
    message: string,
  ): string =>
    `用户${userId}:${username} [${sessionId}] ${method} ${url}: ${message}`;

  static readonly API_LOG_RESPONSE_TIME = (
    method: string,
    url: string,
    responseTime: number,
  ): string => `${method} ${url} 使用了${responseTime}ms`;

  static readonly API_LOG_QUEUE_SEND_FAILED = (message: string): string =>
    `发送 API 日志到队列失败: ${message}`;

  static readonly API_LOG_QUEUE_SENT = (message: string): string =>
    `API 日志已发送到队列: ${message}`;

  static readonly API_LOG_QUEUE_ERROR = (message: string): string =>
    `向消息队列发送 API 日志出错: ${message}`;

  static readonly ARTICLE_NOT_FOUND_BY_ID = (id: number): string =>
    `文章 ID ${id} 未找到`;

  static readonly OSS_UPLOAD_ERROR_MESSAGE = (message: string): string =>
    `上传阿里云OSS错误: ${message}`;

  static readonly API_LOG_CLEANUP_COMPLETED = (deletedCount: number): string =>
    `API 日志清理完成，删除了 ${deletedCount} 条超过1个月的日志`;

  static readonly API_LOG_CLEANUP_FAILED = (errorMessage: string): string =>
    `清理 API 日志失败: ${errorMessage}`;

  static readonly ARTICLE_LOG_CLEANUP_COMPLETED = (
    deletedCount: number,
  ): string => `文章日志清理完成，删除了 ${deletedCount} 条超过1个月的日志`;

  static readonly ARTICLE_LOG_CLEANUP_FAILED = (errorMessage: string): string =>
    `清理文章日志失败: ${errorMessage}`;

  static readonly LOCAL_IP_CONVERTED = (registrationIp: string): string =>
    `本地 IP 已转换为: ${registrationIp}`;

  static readonly SERVICE_NO_AVAILABLE_INSTANCE = (
    serviceName: string,
  ): string => `服务 ${serviceName} 无可用实例`;

  static readonly SERVICE_BUSINESS_ERROR_DETAIL = (
    serviceName: string,
    code: string,
    msg: string,
  ): string => `服务 ${serviceName} 返回业务错误: code=${code}, msg=${msg}`;

  static readonly SERVICE_CALL_FAILED_WITH_MSG = (
    serviceName: string,
    errorMsg: string,
  ): string => `调用 ${serviceName} 失败: ${errorMsg}`;

  static readonly SERVICE_CIRCUIT_BREAKER_TRIGGERED = (
    serviceName: string,
  ): string => `调用 ${serviceName} 已触发熔断，直接返回降级结果`;

  static readonly SERVICE_DEGRADED_MSG = (serviceName: string): string =>
    `调用 ${serviceName} 已降级，请稍后再试`;

  static readonly SERVICE_CALL_ERROR = (
    serviceName: string,
    error: string,
  ): string => `调用 ${serviceName} 失败: ${error}`;

  static readonly SERVICE_CALL_FAILED_RETRY_LATER = (
    serviceName: string,
  ): string => `调用 ${serviceName} 失败，请稍后重试`;

  static readonly VERIFICATION_CODE_EMAIL_SENDING = (
    maskedEmail: string,
    type: string,
  ): string => `发送验证码邮件到: ${maskedEmail}, 场景: ${type}`;

  static readonly VERIFICATION_CODE_EMAIL_SENT = (
    maskedEmail: string,
  ): string => `验证码邮件已成功发送到: ${maskedEmail}`;

  static readonly VERIFICATION_CODE_EMAIL_FAILED = (
    maskedEmail: string,
  ): string => `验证码邮件发送失败: ${maskedEmail}`;

  static readonly LOG_CONFIG_LOADED = (path: string): string =>
    `日志配置加载成功，路径: ${path}`;

  static readonly LOG_CONFIG_LOAD_FAILED = (errorMessage: string): string =>
    `加载日志配置失败: ${errorMessage}`;

  static readonly LOG_WRITE_FAILED = (errorMessage: string): string =>
    `写入日志失败: ${errorMessage}`;

  static readonly UPLOAD_IMAGE_START = (filename: string | undefined): string =>
    `uploadImage 开始，文件信息: filename=${filename}`;

  static readonly UPLOAD_FILE_TYPE_INFO = (
    type: string,
    hasReadable: unknown,
    hasPipe: unknown,
  ): string =>
    `文件对象类型: ${type}, 是否有 readable: ${String(hasReadable)}, 是否有 pipe: ${String(hasPipe)}`;

  static readonly UPLOAD_FILE_KEYS = (keys: string): string =>
    `文件对象键: ${keys}`;

  static readonly UPLOAD_GENERATED_FILENAME = (filename: string): string =>
    `生成唯一文件名: ${filename}`;

  static readonly UPLOAD_FILE_SAVED_TO_TEMP = (path: string): string =>
    `文件已保存到临时目录: ${path}`;

  static readonly UPLOAD_OSS_TARGET_PATH = (path: string): string =>
    `OSS 目标路径: ${path}`;

  static readonly UPLOAD_OSS_COMPLETED = (url: string): string =>
    `OSS 上传完成，URL: ${url}`;

  static readonly UPLOAD_PDF_START = (filename: string | undefined): string =>
    `uploadPdf 开始，文件信息: filename=${filename}`;

  static readonly UPLOAD_UNSUPPORTED_FORMAT = (
    ext: string,
    allowedFormats: string,
  ): string => `不支持的文件格式: ${ext}，允许格式: ${allowedFormats}`;

  static readonly UPLOAD_ALLOWED_FORMATS = (formats: string): string =>
    `仅支持以下格式: ${formats}`;

  static readonly UPLOAD_CHECK_FILE_PROPERTY = (type: string): string =>
    `检查 file.file 属性, 类型: ${type}`;

  static readonly UPLOAD_USE_FILE_STREAM = (
    type: string,
    hasPipe: unknown,
  ): string =>
    `使用 file.file 作为流, 类型: ${type}, 是否有 pipe: ${String(hasPipe)}`;

  static readonly UPLOAD_SAVE_TO_TEMP_FAILED = (message: string): string =>
    `保存文件到临时目录失败: ${message}`;

  static readonly UPLOAD_TEMP_FILE_DELETED = (path: string): string =>
    `临时文件已删除: ${path}`;

  static readonly UPLOAD_DELETE_TEMP_FAILED = (message: string): string =>
    `删除临时文件失败: ${message}`;

  static readonly OSS_UPLOAD_START_DETAIL = (
    localFile: string,
    ossFile: string,
  ): string => `开始上传文件到 OSS: localFile=${localFile}, ossFile=${ossFile}`;

  static readonly OSS_CLIENT_CONFIG_INFO = (
    bucket: string,
    endpoint: string,
  ): string => `OSS 客户端配置: bucket=${bucket}, endpoint=${endpoint}`;

  static readonly OSS_CHECK_FILE_EXISTS = (localFile: string): string =>
    `检查本地文件是否存在: ${localFile}`;

  static readonly OSS_FILE_EXISTS_RESULT = (exists: boolean): string =>
    `文件存在性检查结果: ${exists}`;

  static readonly OSS_LOCAL_FILE_NOT_FOUND = (localFile: string): string =>
    `本地文件不存在: ${localFile}`;

  static readonly OSS_LOCAL_FILE_SIZE = (size: number): string =>
    `本地文件大小: ${size} bytes`;

  static readonly OSS_PUT_RESULT_INFO = (result: string): string =>
    `OSS put 返回结果: ${result}`;

  static readonly OSS_FILE_UPLOAD_SUCCESS = (url: string): string =>
    `OSS 文件上传成功: ${url}`;

  static readonly OSS_UPLOAD_ERROR_LOG = (message: string): string =>
    `OSS 上传失败: ${message}`;

  static readonly OSS_UPLOAD_ERROR_DETAIL_INFO = (
    localFile: string,
    ossFile: string,
  ): string => `失败的 localFile: ${localFile}, ossFile: ${ossFile}`;

  static readonly OSS_UPLOAD_ERROR_STACK_INFO = (stack: string): string =>
    `错误堆栈: ${stack}`;

  static readonly TABLE_SETTINGS_UPDATED = (
    userId: number,
    tableKey: string,
  ): string => `用户 ${userId} 更新了页面 ${tableKey} 的列设置`;

  static readonly TABLE_SETTINGS_CREATED = (
    userId: number,
    tableKey: string,
  ): string => `用户 ${userId} 创建了页面 ${tableKey} 的列设置`;

  static readonly TABLE_SETTINGS_DELETED = (
    userId: number,
    tableKey: string,
  ): string => `用户 ${userId} 删除了页面 ${tableKey} 的列设置`;

  // ===== 日志攒批 =====

  static readonly API_LOG_BATCH_ENQUEUED = (size: number): string =>
    `ApiLog 已入队攒批，当前缓冲区: ${size} 条`;

  static readonly ARTICLE_LOG_BATCH_ENQUEUED = (size: number): string =>
    `ArticleLog 已入队攒批，当前缓冲区: ${size} 条`;

  static readonly BATCH_FLUSH_FAILED = (error: string): string =>
    `攒批写入失败: ${error}`;

  static readonly BATCH_INITIALIZED = (
    name: string,
    batchSize: number,
    intervalMs: number,
  ): string =>
    `[攒批] ${name} 初始化完成 (batchSize=${batchSize}, interval=${intervalMs}ms)`;

  static readonly BATCH_DISCARDED_AFTER_SHUTDOWN = (name: string): string =>
    `[攒批] ${name} 已关闭，丢弃数据`;

  static readonly BATCH_FORCE_FLUSH_MAX_CAPACITY = (
    name: string,
    maxBufferSize: number,
  ): string => `[攒批] ${name} 缓冲区达到最大容量 ${maxBufferSize}，强制 flush`;

  static readonly BATCH_FLUSH_SUCCESS = (
    name: string,
    batchSize: number,
  ): string => `[攒批] ${name} flush 成功，批次大小: ${batchSize}`;

  static readonly BATCH_FLUSH_FAILED_DETAIL = (
    name: string,
    batchSize: number,
    errorMessage: string,
  ): string =>
    `[攒批] ${name} flush 失败，批次大小: ${batchSize}，错误: ${errorMessage}`;

  static readonly BATCH_SHUTDOWN_FLUSH_REMAINING = (
    name: string,
    remaining: number,
  ): string => `[攒批] ${name} 优雅关闭，flush 剩余 ${remaining} 条数据`;

  static readonly BATCH_SHUTDOWN_COMPLETED = (name: string): string =>
    `[攒批] ${name} 已关闭`;

  static readonly INTERNAL_TOKEN_SECRET_NOT_CONFIGURED = "内部令牌密钥未配置";

  static readonly INTERNAL_TOKEN_MISSING = "请求头中缺少内部令牌";

  static readonly INTERNAL_TOKEN_INVALID = "内部令牌无效";

  static readonly INTERNAL_TOKEN_EXPIRED = "内部令牌已过期";

  static readonly SERVICE_NAME_MISMATCH = "服务名称不匹配";

  // ===== RabbitMQ =====

  static readonly API_RABBITMQ_START = "启动 ApiLog RabbitMQ 消息监听";

  static readonly API_SAVE = "API 日志已保存到数据库";

  static readonly ARTICLE_RABBITMQ_START = "启动 ArticleLog RabbitMQ 消息监听";

  static readonly ARTICLE_HANDLER = "ArticleLog 消息处理完成";

  static readonly ARTICLE_LESS_ACTION = "ArticleLog 消息缺少 action 字段";

  static readonly ARTICLE_LESS_CONTNET = "ArticleLog 消息缺少 content 字段";

  static readonly ARTICLE_SAVE = "ArticleLog 写入成功";

  static readonly EMPTY_FILE_PATH = "未配置文件保存路径";

  static readonly RABBITMQ_CONNECTION = "RabbitMQ连接成功";

  // ===== 定时任务 =====

  static readonly TASK_CLEAN = "开始清理超过1个月的 API 日志";

  static readonly TASK_ARTICLE_CLEAN = "开始清理超过1个月的文章日志";

  // ===== 通用错误消息 =====

  static readonly ERROR_DEFAULT_MSG = "NestJS服务器错误";

  static readonly PARAM_ERROR = "参数解析失败";

  static readonly UNAUTHORIZED_USER = "未授权的用户，无法访问";

  static readonly NO_ADMIN_USER = "当前用户没有管理员权限，无法访问此功能";

  static readonly UNKNOWN_USERNAME = "unknown";

  static readonly UNKNOWN_USER = "未知用户";

  static readonly UNKNOWN_ERROR = "未知错误";

  static readonly UNKNOWN_ARTICLE = "未知文章";

  // ===== 日志模块消息 =====

  static readonly ARTICLE_LOG_NOT_FOUND = "文章日志记录不存在";

  static readonly ARTICLE_LOG_PARTIAL_NOT_FOUND =
    "部分或全部文章日志记录不存在";

  static readonly API_LOG_NOT_FOUND = "API日志记录不存在";

  static readonly API_LOG_PARTIAL_NOT_FOUND = "部分或全部API日志记录不存在";

  // ===== Nacos =====

  static readonly REGISTER_NACOS = "注册到 nacos 成功";

  static readonly REGISTER_NACOS_DEV_MODE =
    "SERVER_MODE=dev，Nacos 注册统一使用 127.0.0.1";

  static readonly NACOS_HOST_NOT_CONFIGURED = "Nacos 服务地址未配置";

  static readonly NACOS_PORT_NOT_CONFIGURED = "Nacos 服务端口未配置";

  static readonly SERVER_MODE_NOT_CONFIGURED = "服务运行模式未配置";

  // ===== GitHub 登录 =====

  static readonly GITHUB_LOGIN_PROCESS_FAILED_PREFIX = "GitHub 登录处理失败: ";

  static readonly GITHUB_REDIS_UNAVAILABLE =
    "Redis 未配置，无法发起 GitHub 登录";

  static readonly GITHUB_AUTH_PARAMS_MISSING = "GitHub 授权参数缺失";

  static readonly GITHUB_AUTH_CANCELLED_OR_FAILED = "GitHub 授权已取消或失败";

  static readonly GITHUB_OAUTH_CONFIG_INCOMPLETE_PREFIX =
    "GitHub OAuth 配置不完整，缺少 ";

  static readonly GITHUB_REDIS_STATE_UNAVAILABLE =
    "Redis 未配置，无法处理 GitHub 登录状态";

  static readonly GITHUB_STATE_EXPIRED = "GitHub 授权状态已过期，请重新登录";

  static readonly GITHUB_STATE_PARSE_FAILED =
    "GitHub 授权状态解析失败，请重新登录";

  static readonly GITHUB_ACCESS_TOKEN_FAILED = "GitHub 访问令牌获取失败";

  static readonly GITHUB_USER_PROFILE_FAILED = "GitHub 用户资料获取失败";

  static readonly GITHUB_USER_PROFILE_INVALID = "GitHub 用户资料不完整";

  static readonly GITHUB_SPRING_TOKEN_TICKET_FAILED =
    "Spring 未正确返回 GitHub 登录票据";

  static readonly GITHUB_SPRING_TOKEN_TICKET_MISSING =
    "Spring 未返回 GitHub 登录票据";

  // ===== 熔断器 =====

  static readonly SERVICE_CIRCUIT_BREAKER_OPEN = (
    serviceName: string,
  ): string => `服务 ${serviceName} 的熔断器已打开`;

  static readonly SERVICE_CIRCUIT_BREAKER_HALF_OPEN = (
    serviceName: string,
  ): string => `服务 ${serviceName} 的熔断器进入半开状态`;

  static readonly SERVICE_CIRCUIT_BREAKER_CLOSE = (
    serviceName: string,
  ): string => `服务 ${serviceName} 的熔断器已关闭`;

  static readonly SERVICE_CIRCUIT_BREAKER_FALLBACK = (
    serviceName: string,
    result: unknown,
  ): string =>
    `服务 ${serviceName} 触发熔断降级，返回结果: ${JSON.stringify(result)}`;

  static readonly SERVICE_RETRY = (
    url: string,
    retryCount: number,
    message: string,
  ): string => `请求 ${url} 第 ${retryCount} 次重试，原因: ${message}`;

  // ===== 启动/测试 =====

  static readonly TEST_WELCOME = "Hello,I am Nest.js!";

  static readonly START_WELCOME = "NestJS应用已启动";

  // ===== OSS =====

  static readonly OSS_UPLOAD_ERR = "上传阿里云OSS错误";

  static readonly OSS_CONFIG_INCOMPLETE =
    "OSS 配置不完整，请检查 application.yaml 中的 oss 配置";

  static readonly OSS_PUT_OPERATION_START = "开始执行 OSS put 操作...";

  static readonly OSS_UPLOAD_FAILED = "OSS 上传失败";

  static readonly OSS_BUN_RUNTIME_COMPAT_MESSAGE =
    "检测到 Bun 运行时，OSS 上传将使用兼容实现";

  static readonly OSS_CLIENT_NOT_INITIALIZED = "OSS 客户端尚未初始化";

  static readonly OSS_PUT_OPERATION_TIMEOUT = "OSS put 操作超时";

  static readonly OSS_RESPONSE_NON_SUCCESS_PREFIX = "OSS 返回非成功状态码";

  static readonly OSS_RESPONSE_CONTENT_PREFIX = "响应内容:";

  // ===== 文件上传 =====

  static readonly FILE_SAVE_TEMP_START = "开始保存文件到临时目录...";

  static readonly FILE_UPLOAD_OSS_START = "开始上传文件到 OSS...";

  static readonly FILE_CLEANUP_START = "开始清理临时文件...";

  static readonly FILE_CLEANUP_COMPLETED = "临时文件清理完成";

  static readonly ONLY_PDF_SUPPORTED = "只支持上传 PDF 文件";

  static readonly NO_FILE_UPLOADED = "未上传文件";

  static readonly USING_TO_BUFFER_METHOD = "使用 toBuffer() 方法读取文件";

  static readonly FILE_NO_VALID_METHOD =
    "文件对象既没有 file 属性也没有 toBuffer 方法";

  static readonly WORD_FILE_PATH_NOT_CONFIGURED = "Word 文件保存路径未配置";

  static readonly FILE_PART_NOT_FOUND = "未找到文件部分";

  // ===== 邮件 =====

  static readonly EMAIL_VERIFICATION_CODE_SUBJECT = "邮箱验证码";

  static readonly EMAIL_VERIFICATION_CODE_REGISTER_SUBJECT = "注册验证码";

  static readonly EMAIL_VERIFICATION_CODE_LOGIN_SUBJECT = "登录验证码";

  static readonly EMAIL_VERIFICATION_CODE_RESET_SUBJECT = "重置密码验证码";

  static readonly MAIL_SERVICE_CONFIG_INCOMPLETE =
    "邮件 SMTP 配置不完整，邮件服务不可用";

  static readonly MAIL_SERVICE_CONFIG_INCORRECT =
    "邮件服务未正确配置，请检查 SMTP 配置";

  // ===== Redis 分布式锁消息 =====

  static readonly REDIS_LOCK_ACQUIRE_SUCCESS = "获取分布式锁成功，key: %s";

  static readonly REDIS_LOCK_ACQUIRE_FAIL =
    "获取分布式锁失败，跳过本次执行，key: %s";

  static readonly REDIS_LOCK_RELEASE_SUCCESS = "释放分布式锁成功，key: %s";

  static readonly REDIS_LOCK_RELEASE_FAIL = "释放分布式锁失败，key: %s";

  // ===== MongoDB 工具消息 =====

  static readonly MONGO_COLLECTION_NOT_ALLOWED_MSG = (
    collectionName: string,
  ): string => `不允许查询集合: ${collectionName}`;

  static readonly MONGO_FORBIDDEN_OPERATOR_MSG = (key: string): string =>
    `不允许使用操作符: ${key}`;

  // ===== SQL 代理工具消息 =====

  static readonly SQL_PROXY_QUERY_MUST_BE_STRING = "SQL查询语句必须是字符串";

  static readonly SQL_PROXY_QUERY_NOT_EMPTY = "SQL查询语句不能为空";

  static readonly SQL_PROXY_PARAMS_MUST_BE_OBJECT = "参数必须是对象";

  static readonly SQL_PROXY_FORBIDDEN_STATEMENT =
    "安全限制：只允许执行只读查询（SELECT/WITH/SHOW/DESC/DESCRIBE/EXPLAIN）";

  static readonly SQL_PROXY_TABLE_NOT_ALLOWED = (tableName: string): string =>
    `安全限制：表 '${tableName}' 不在白名单内`;

  static readonly SQL_PROXY_LIMIT_REQUIRED =
    "安全限制：SQL查询必须包含LIMIT子句";

  static readonly SQL_PROXY_LIMIT_EXCEEDED = "安全限制：LIMIT超过最大限制100";

  static readonly SQL_PROXY_MULTIPLE_STATEMENTS =
    "安全限制：禁止执行多条SQL语句";

  static readonly SQL_PROXY_QUERY_FAILED = (message: string): string =>
    `执行SQL查询失败: ${message}`;

  static readonly SQL_PROXY_TABLE_SCHEMA_FAILED = (message: string): string =>
    `获取表结构信息失败: ${message}`;
}
