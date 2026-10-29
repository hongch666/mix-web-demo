/**
 * 消息常量类
 */
export class Messages {
  // ===== 内部令牌 =====

  /** 构造内部令牌服务名不匹配的错误消息 */
  static readonly INTERNAL_TOKEN_SERVICE_NAME_MISMATCH = (
    requiredServiceName: string,
    actualServiceName: string,
  ): string =>
    `${this.SERVICE_NAME_MISMATCH}. 期望: ${requiredServiceName}, 获得: ${actualServiceName}`;

  /** 构造内部令牌校验成功的日志消息 */
  static readonly INTERNAL_TOKEN_VERIFICATION_SUCCESS = (
    userId: number,
    serviceName: string,
  ): string => `内部令牌验证成功 - 用户ID: ${userId}, 服务: ${serviceName}`;

  /** 构造内部令牌校验失败的错误消息 */
  static readonly INTERNAL_TOKEN_VERIFICATION_FAILED = (
    message: string,
  ): string => `令牌验证失败: ${message}`;

  // ===== 启动信息 =====

  /** 构造运行模式的启动提示 */
  static readonly STARTUP_SERVER_MODE = (mode: string): string =>
    `运行模式: ${mode}`;

  /** 构造服务监听地址的启动提示 */
  static readonly STARTUP_SERVICE_ADDRESS = (
    ip: string,
    port: number,
  ): string => `服务地址: http://${ip}:${port}`;

  /** 构造 Swagger 文档地址的启动提示 */
  static readonly STARTUP_SWAGGER_ADDRESS = (
    ip: string,
    port: number,
  ): string => `Swagger文档地址: http://${ip}:${port}/api-docs`;

  // ===== 文章日志消息 =====

  /** 构造接收 Spring 文章日志的日志消息 */
  static readonly ARTICLE_LOG_SPRING_MESSAGE = (message: string): string =>
    `接收到 Spring 发送的 ArticleLog 消息: ${message}`;

  /** 构造接收文章日志的日志消息 */
  static readonly ARTICLE_LOG_MESSAGE = (message: string): string =>
    `接收到 ArticleLog 消息: ${message}`;

  /** 构造处理文章日志失败的错误消息 */
  static readonly ARTICLE_LOG_PROCESS_FAILED = (message: string): string =>
    `处理 ArticleLog 消息失败: ${message}`;

  /** 构造文章日志缺少 action 字段的错误消息 */
  static readonly ARTICLE_LOG_MISSING_ACTION = (message: string): string =>
    `ArticleLog 消息缺少 action 字段: ${message}`;

  /** 构造文章日志缺少 content 字段的错误消息 */
  static readonly ARTICLE_LOG_MISSING_CONTENT = (message: string): string =>
    `ArticleLog 消息缺少 content 字段: ${message}`;

  /** 构造文章日志动作类型无效的错误消息 */
  static readonly ARTICLE_LOG_INVALID_ACTION = (action: string): string =>
    `无效的操作类型: ${action}`;

  /** 构造文章日志 action 取值非法的错误消息 */
  static readonly ARTICLE_LOG_INVALID_ACTION_DETAIL = (
    action: string,
  ): string => `ArticleLog 消息包含无效的 action 值: ${action}`;

  /** 构造准备保存文章日志的日志消息 */
  static readonly ARTICLE_LOG_PREPARE_SAVE = (message: string): string =>
    `准备保存 ArticleLog: ${message}`;

  // ===== API 日志消息 =====

  /** 构造接收 Spring API 日志的日志消息 */
  static readonly API_LOG_SPRING_MESSAGE = (message: string): string =>
    `接收到 Spring 发送的 ApiLog 消息: ${message}`;

  /** 构造接收 API 日志的日志消息 */
  static readonly API_LOG_MESSAGE = (message: string): string =>
    `接收到 ApiLog 消息: ${message}`;

  /** 构造非 API 日志格式消息被忽略的日志消息 */
  static readonly API_LOG_IGNORED_MESSAGE = (message: string): string =>
    `收到非 API 日志格式的消息，已忽略: ${message}`;

  /** 构造响应时间异常被修正为 0 的日志消息 */
  static readonly API_LOG_RESPONSE_TIME_CORRECTED = (
    responseTime: number,
  ): string => `接口响应时间为${responseTime}，已将其设置为0: `;

  /** 构造处理 API 日志失败的错误消息 */
  static readonly API_LOG_PROCESS_FAILED = (message: string): string =>
    `处理 ApiLog 消息失败: ${message}`;

  /** 构造 API 日志索引创建成功的日志消息 */
  static readonly API_LOG_INDEX_CREATED = (indexName: string): string =>
    `ApiLog 索引已创建: ${indexName}`;

  /** 构造 API 日志索引初始化失败的错误消息 */
  static readonly API_LOG_INDEX_INIT_FAILED = (message: string): string =>
    `ApiLog 索引初始化失败: ${message}`;

  /** 构造文章日志索引创建成功的日志消息 */
  static readonly ARTICLE_LOG_INDEX_CREATED = (indexName: string): string =>
    `索引已创建: ${indexName}`;

  /** 构造文章日志索引初始化失败的错误消息 */
  static readonly ARTICLE_LOG_INDEX_INIT_FAILED = (message: string): string =>
    `文章日志索引初始化失败: ${message}`;

  // ===== 异常与请求日志 =====

  /** 构造全局异常日志的结构化消息 */
  static readonly EXCEPTION_LOG = (
    method: string,
    url: string,
    errorIdentifier: string,
    message: string,
    stack: string | undefined,
  ): string =>
    `[${method}] ${url} - [${errorIdentifier}] ${message} - ${stack}`;

  /** 构造接口请求日志的结构化消息 */
  static readonly API_LOG_REQUEST = (
    userId: number,
    username: string,
    sessionId: string,
    method: string,
    url: string,
    message: string,
  ): string =>
    `用户${userId}:${username} [${sessionId}] ${method} ${url}: ${message}`;

  /** 构造接口响应耗时的日志消息 */
  static readonly API_LOG_RESPONSE_TIME = (
    method: string,
    url: string,
    responseTime: number,
  ): string => `${method} ${url} 使用了${responseTime}ms`;

  /** 构造 API 日志入队失败的错误消息 */
  static readonly API_LOG_QUEUE_SEND_FAILED = (message: string): string =>
    `发送 API 日志到队列失败: ${message}`;

  /** 构造 API 日志入队成功的日志消息 */
  static readonly API_LOG_QUEUE_SENT = (message: string): string =>
    `API 日志已发送到队列: ${message}`;

  /** 构造 API 日志队列处理异常的错误消息 */
  static readonly API_LOG_QUEUE_ERROR = (message: string): string =>
    `向消息队列发送 API 日志出错: ${message}`;

  // ===== 业务与运维提示 =====

  /** 构造按文章 ID 查不到文章的消息 */
  static readonly ARTICLE_NOT_FOUND_BY_ID = (id: number): string =>
    `文章 ID ${id} 未找到`;

  /** 构造 OSS 上传失败的错误消息 */
  static readonly OSS_UPLOAD_ERROR_MESSAGE = (message: string): string =>
    `上传阿里云OSS错误: ${message}`;

  /** 构造 API 日志清理完成的日志消息 */
  static readonly API_LOG_CLEANUP_COMPLETED = (deletedCount: number): string =>
    `API 日志清理完成，删除了 ${deletedCount} 条超过3个月的日志`;

  /** 构造 API 日志清理失败的错误消息 */
  static readonly API_LOG_CLEANUP_FAILED = (errorMessage: string): string =>
    `清理 API 日志失败: ${errorMessage}`;

  /** 构造本机 IP 转换结果的日志消息 */
  static readonly LOCAL_IP_CONVERTED = (registrationIp: string): string =>
    `本地 IP 已转换为: ${registrationIp}`;

  // ===== 远程调用与降级 =====

  /** 构造没有可用服务实例的错误消息 */
  static readonly SERVICE_NO_AVAILABLE_INSTANCE = (
    serviceName: string,
  ): string => `服务 ${serviceName} 无可用实例`;

  /** 构造下游业务错误的详情消息 */
  static readonly SERVICE_BUSINESS_ERROR_DETAIL = (
    serviceName: string,
    code: string,
    msg: string,
  ): string => `服务 ${serviceName} 返回业务错误: code=${code}, msg=${msg}`;

  /** 构造带下游错误信息的调用失败消息 */
  static readonly SERVICE_CALL_FAILED_WITH_MSG = (
    serviceName: string,
    errorMsg: string,
  ): string => `调用 ${serviceName} 失败: ${errorMsg}`;

  /** 构造熔断器触发的降级消息 */
  static readonly SERVICE_CIRCUIT_BREAKER_TRIGGERED = (
    serviceName: string,
  ): string => `调用 ${serviceName} 已触发熔断，直接返回降级结果`;

  /** 构造服务降级返回给调用方的消息 */
  static readonly SERVICE_DEGRADED_MSG = (serviceName: string): string =>
    `调用 ${serviceName} 已降级，请稍后再试`;

  /** 构造服务调用异常的错误消息 */
  static readonly SERVICE_CALL_ERROR = (
    serviceName: string,
    error: string,
  ): string => `调用 ${serviceName} 失败: ${error}`;

  /** 构造服务调用失败请稍后重试的提示 */
  static readonly SERVICE_CALL_FAILED_RETRY_LATER = (
    serviceName: string,
  ): string => `调用 ${serviceName} 失败，请稍后重试`;

  // ===== 邮件验证码 =====

  /** 构造发送邮箱验证码预处理失败的消息 */
  static readonly VERIFICATION_CODE_EMAIL_SENDING = (
    maskedEmail: string,
    type: string,
  ): string => `发送验证码邮件到: ${maskedEmail}, 场景: ${type}`;

  /** 构造邮箱验证码发送成功的日志消息 */
  static readonly VERIFICATION_CODE_EMAIL_SENT = (
    maskedEmail: string,
  ): string => `验证码邮件已成功发送到: ${maskedEmail}`;

  /** 构造邮箱验证码发送失败的错误消息 */
  static readonly VERIFICATION_CODE_EMAIL_FAILED = (
    maskedEmail: string,
  ): string => `验证码邮件发送失败: ${maskedEmail}`;

  // ===== 进程内日志 =====

  /** 构造日志配置加载成功的日志消息 */
  static readonly LOG_CONFIG_LOADED = (path: string): string =>
    `日志配置加载成功，路径: ${path}`;

  /** 构造日志配置加载失败的错误消息 */
  static readonly LOG_CONFIG_LOAD_FAILED = (errorMessage: string): string =>
    `加载日志配置失败: ${errorMessage}`;

  /** 构造日志写入失败的错误消息 */
  static readonly LOG_WRITE_FAILED = (errorMessage: string): string =>
    `写入日志失败: ${errorMessage}`;

  /** 构造 MongoDB 查询调试日志 */
  static readonly MONGO_DEBUG_LOG = (
    collectionName: string,
    methodName: string,
    args: string,
  ): string => `Mongoose: ${collectionName}.${methodName}(${args})`;

  // ===== 文件上传 =====

  /** 构造图片上传开始的日志消息 */
  static readonly UPLOAD_IMAGE_START = (filename: string | undefined): string =>
    `uploadImage 开始，文件信息: filename=${filename}`;

  /** 构造上传文件类型信息的调试日志 */
  static readonly UPLOAD_FILE_TYPE_INFO = (
    type: string,
    hasReadable: unknown,
    hasPipe: unknown,
  ): string =>
    `文件对象类型: ${type}, 是否有 readable: ${String(hasReadable)}, 是否有 pipe: ${String(hasPipe)}`;

  /** 构造上传文件字段名的调试日志 */
  static readonly UPLOAD_FILE_KEYS = (keys: string): string =>
    `文件对象键: ${keys}`;

  /** 构造生成文件名结果的日志消息 */
  static readonly UPLOAD_GENERATED_FILENAME = (filename: string): string =>
    `生成唯一文件名: ${filename}`;

  /** 构造文件写入临时目录的日志消息 */
  static readonly UPLOAD_FILE_SAVED_TO_TEMP = (path: string): string =>
    `文件已保存到临时目录: ${path}`;

  /** 构造 OSS 目标路径的日志消息 */
  static readonly UPLOAD_OSS_TARGET_PATH = (path: string): string =>
    `OSS 目标路径: ${path}`;

  /** 构造 OSS 上传完成的日志消息 */
  static readonly UPLOAD_OSS_COMPLETED = (url: string): string =>
    `OSS 上传完成，URL: ${url}`;

  /** 构造 PDF 上传开始的日志消息 */
  static readonly UPLOAD_PDF_START = (filename: string | undefined): string =>
    `uploadPdf 开始，文件信息: filename=${filename}`;

  /** 构造上传格式不支持的错误消息 */
  static readonly UPLOAD_UNSUPPORTED_FORMAT = (
    ext: string,
    allowedFormats: string,
  ): string => `不支持的文件格式: ${ext}，允许格式: ${allowedFormats}`;

  /** 构造允许上传格式清单的提示 */
  static readonly UPLOAD_ALLOWED_FORMATS = (formats: string): string =>
    `仅支持以下格式: ${formats}`;

  /** 构造文件字段类型判断的调试日志 */
  static readonly UPLOAD_CHECK_FILE_PROPERTY = (type: string): string =>
    `检查 file.file 属性, 类型: ${type}`;

  /** 构造使用文件流方式处理的日志消息 */
  static readonly UPLOAD_USE_FILE_STREAM = (
    type: string,
    hasPipe: unknown,
  ): string =>
    `使用 file.file 作为流, 类型: ${type}, 是否有 pipe: ${String(hasPipe)}`;

  /** 构造文件写入临时目录失败的错误消息 */
  static readonly UPLOAD_SAVE_TO_TEMP_FAILED = (message: string): string =>
    `保存文件到临时目录失败: ${message}`;

  /** 构造临时文件删除成功的日志消息 */
  static readonly UPLOAD_TEMP_FILE_DELETED = (path: string): string =>
    `临时文件已删除: ${path}`;

  /** 构造临时文件删除失败的错误消息 */
  static readonly UPLOAD_DELETE_TEMP_FAILED = (message: string): string =>
    `删除临时文件失败: ${message}`;

  // ===== OSS 上传 =====

  /** 构造 OSS 上传开始的详细日志 */
  static readonly OSS_UPLOAD_START_DETAIL = (
    localFile: string,
    ossFile: string,
  ): string => `开始上传文件到 OSS: localFile=${localFile}, ossFile=${ossFile}`;

  /** 构造 OSS 客户端配置信息的日志消息 */
  static readonly OSS_CLIENT_CONFIG_INFO = (
    bucket: string,
    endpoint: string,
  ): string => `OSS 客户端配置: bucket=${bucket}, endpoint=${endpoint}`;

  /** 构造检查 OSS 文件是否存在的日志消息 */
  static readonly OSS_CHECK_FILE_EXISTS = (localFile: string): string =>
    `检查本地文件是否存在: ${localFile}`;

  /** 构造 OSS 文件存在性判断结果的日志消息 */
  static readonly OSS_FILE_EXISTS_RESULT = (exists: boolean): string =>
    `文件存在性检查结果: ${exists}`;

  /** 构造本地待上传文件不存在的日志消息 */
  static readonly OSS_LOCAL_FILE_NOT_FOUND = (localFile: string): string =>
    `本地文件不存在: ${localFile}`;

  /** 构造本地文件大小的日志消息 */
  static readonly OSS_LOCAL_FILE_SIZE = (size: number): string =>
    `本地文件大小: ${size} bytes`;

  /** 构造 OSS put 返回结果的日志消息 */
  static readonly OSS_PUT_RESULT_INFO = (result: string): string =>
    `OSS put 返回结果: ${result}`;

  /** 构造 OSS 上传成功后的地址日志 */
  static readonly OSS_FILE_UPLOAD_SUCCESS = (url: string): string =>
    `OSS 文件上传成功: ${url}`;

  /** 构造 OSS 上传失败的错误日志 */
  static readonly OSS_UPLOAD_ERROR_LOG = (message: string): string =>
    `OSS 上传失败: ${message}`;

  /** 构造 OSS 上传失败的详情日志 */
  static readonly OSS_UPLOAD_ERROR_DETAIL_INFO = (
    localFile: string,
    ossFile: string,
  ): string => `失败的 localFile: ${localFile}, ossFile: ${ossFile}`;

  /** 构造 OSS 上传失败的堆栈日志 */
  static readonly OSS_UPLOAD_ERROR_STACK_INFO = (stack: string): string =>
    `错误堆栈: ${stack}`;

  // ===== SQL 工具表配置 =====

  /** 构造 SQL 工具表配置更新的日志消息 */
  static readonly TABLE_SETTINGS_UPDATED = (
    userId: number,
    tableKey: string,
  ): string => `用户 ${userId} 更新了页面 ${tableKey} 的列设置`;

  /** 构造 SQL 工具表配置新增的日志消息 */
  static readonly TABLE_SETTINGS_CREATED = (
    userId: number,
    tableKey: string,
  ): string => `用户 ${userId} 创建了页面 ${tableKey} 的列设置`;

  /** 构造 SQL 工具表配置删除的日志消息 */
  static readonly TABLE_SETTINGS_DELETED = (
    userId: number,
    tableKey: string,
  ): string => `用户 ${userId} 删除了页面 ${tableKey} 的列设置`;

  // ===== 权限校验 =====

  /** 构造越权访问其他用户数据的拒绝消息 */
  static readonly USER_SCOPE_DENIED = (
    currentUserId: number,
    targetUserId: number,
  ): string =>
    `用户作用域校验未通过: 当前用户 ${currentUserId}, 目标用户 ${targetUserId}`;

  /** 构造管理员跨用户访问的审计日志 */
  static readonly USER_SCOPE_ADMIN_ACCESS = (
    currentUserId: number,
    targetUserId: number,
  ): string =>
    `用户 ${currentUserId} 以管理员身份访问用户 ${targetUserId} 的数据`;

  /** 构造管理员权限校验失败的错误消息 */
  static readonly ADMIN_PERMISSION_CHECK_FAILED = (message: string): string =>
    `管理员权限校验失败: ${message}`;

  // ===== 日志攒批 =====

  // ===== 日志攒批 =====

  /** 构造 API 日志进入攒批队列的日志消息 */
  static readonly API_LOG_BATCH_ENQUEUED = (size: number): string =>
    `ApiLog 已入队攒批，当前缓冲区: ${size} 条`;

  /** 构造文章日志进入攒批队列的日志消息 */
  static readonly ARTICLE_LOG_BATCH_ENQUEUED = (size: number): string =>
    `ArticleLog 已入队攒批，当前缓冲区: ${size} 条`;

  /** 构造攒批刷写失败的错误消息 */
  static readonly BATCH_FLUSH_FAILED = (error: string): string =>
    `攒批写入失败: ${error}`;

  /** 构造攒批缓冲区初始化的日志消息 */
  static readonly BATCH_INITIALIZED = (
    name: string,
    batchSize: number,
    intervalMs: number,
  ): string =>
    `[攒批] ${name} 初始化完成 (batchSize=${batchSize}, interval=${intervalMs}ms)`;

  /** 构造关停后丢弃攒批数据的日志消息 */
  static readonly BATCH_DISCARDED_AFTER_SHUTDOWN = (name: string): string =>
    `[攒批] ${name} 已关闭，丢弃数据`;

  /** 构造缓冲区超限强制刷写的日志消息 */
  static readonly BATCH_FORCE_FLUSH_MAX_CAPACITY = (
    name: string,
    maxBufferSize: number,
  ): string => `[攒批] ${name} 缓冲区达到最大容量 ${maxBufferSize}，强制 flush`;

  /** 构造攒批刷写成功的日志消息 */
  static readonly BATCH_FLUSH_SUCCESS = (
    name: string,
    batchSize: number,
  ): string => `[攒批] ${name} flush 成功，批次大小: ${batchSize}`;

  /** 构造攒批刷写失败后安排重试的日志消息 */
  static readonly BATCH_FLUSH_RETRY_SCHEDULED = (
    name: string,
    batchSize: number,
    retryCount: number,
    maxRetries: number,
    errorMessage: string,
  ): string =>
    `[攒批] ${name} flush 失败，批次大小: ${batchSize}，已放回缓冲区头部等待第 ${retryCount}/${maxRetries} 次重试，错误: ${errorMessage}`;

  /** 构造重试耗尽后丢弃攒批数据的日志消息 */
  static readonly BATCH_FLUSH_DROPPED_AFTER_RETRIES = (
    name: string,
    batchSize: number,
    retryCount: number,
    errorMessage: string,
  ): string =>
    `[攒批] ${name} flush 连续失败 ${retryCount} 次，丢弃批次大小: ${batchSize}，错误: ${errorMessage}`;

  /** 构造关停时丢弃未刷写数据的日志消息 */
  static readonly BATCH_FLUSH_DROPPED_ON_SHUTDOWN = (
    name: string,
    batchSize: number,
    errorMessage: string,
  ): string =>
    `[攒批] ${name} 关闭期间 flush 失败，丢弃批次大小: ${batchSize}，错误: ${errorMessage}`;

  /** 构造关停时刷写剩余数据的日志消息 */
  static readonly BATCH_SHUTDOWN_FLUSH_REMAINING = (
    name: string,
    remaining: number,
  ): string => `[攒批] ${name} 优雅关闭，flush 剩余 ${remaining} 条数据`;

  /** 构造攒批组件关停完成的日志消息 */
  static readonly BATCH_SHUTDOWN_COMPLETED = (name: string): string =>
    `[攒批] ${name} 已关闭`;

  // ===== Nacos 注册 =====

  /** 构造 Nacos 注销实例失败的错误消息 */
  static readonly NACOS_DEREGISTER_FAILED = (errorMessage: string): string =>
    `从 nacos 注销实例失败: ${errorMessage}`;

  // ===== GitHub OAuth =====

  /** 构造 GitHub access_token 响应的调试日志 */
  static readonly GITHUB_ACCESS_TOKEN_RESPONSE = (
    status: number,
    errorCode: string,
    errorDescription: string,
    contentType: string,
  ): string =>
    `GitHub 访问令牌响应异常 - HTTP ${status}, error=${errorCode || "unknown"}, description=${errorDescription || "unknown"}, contentType=${contentType || "unknown"}`;

  /** 构造 GitHub access_token 请求失败的错误消息 */
  static readonly GITHUB_ACCESS_TOKEN_REQUEST_FAILED = (
    errorCode: string,
    errorMessage: string,
    status?: number,
  ): string =>
    `GitHub 访问令牌请求失败 - status=${status || "unknown"}, code=${errorCode || "unknown"}, message=${errorMessage}`;

  /** 构造 GitHub 用户资料响应的调试日志 */
  static readonly GITHUB_USER_PROFILE_RESPONSE = (
    status: number,
    message: string,
    contentType: string,
    requestId: string,
  ): string =>
    `GitHub 用户资料响应异常 - HTTP ${status}, message=${message || "unknown"}, contentType=${contentType || "unknown"}, requestId=${requestId || "unknown"}`;

  /** 构造 GitHub 用户资料请求失败的错误消息 */
  static readonly GITHUB_USER_PROFILE_REQUEST_FAILED = (
    errorCode: string,
    errorMessage: string,
    status?: number,
  ): string =>
    `GitHub 用户资料请求失败 - status=${status || "unknown"}, code=${errorCode || "unknown"}, message=${errorMessage}`;

  // ===== 熔断器 =====

  // ===== 熔断与重试 =====

  /** 构造熔断器打开的日志消息 */
  static readonly SERVICE_CIRCUIT_BREAKER_OPEN = (
    serviceName: string,
  ): string => `服务 ${serviceName} 的熔断器已打开`;

  /** 构造熔断器半开的日志消息 */
  static readonly SERVICE_CIRCUIT_BREAKER_HALF_OPEN = (
    serviceName: string,
  ): string => `服务 ${serviceName} 的熔断器进入半开状态`;

  /** 构造熔断器关闭的日志消息 */
  static readonly SERVICE_CIRCUIT_BREAKER_CLOSE = (
    serviceName: string,
  ): string => `服务 ${serviceName} 的熔断器已关闭`;

  /** 构造熔断降级兜底的日志消息 */
  static readonly SERVICE_CIRCUIT_BREAKER_FALLBACK = (
    serviceName: string,
    result: unknown,
  ): string =>
    `服务 ${serviceName} 触发熔断降级，返回结果: ${JSON.stringify(result)}`;

  /** 构造远程调用重试的日志消息 */
  static readonly SERVICE_RETRY = (
    url: string,
    retryCount: number,
    message: string,
  ): string => `请求 ${url} 第 ${retryCount} 次重试，原因: ${message}`;

  // ===== OpenTelemetry =====

  // ===== 链路追踪 =====

  /** 构造无效采样比例的错误消息 */
  static readonly OTEL_INVALID_SAMPLER_RATIO = (ratio: string): string =>
    `无效的 OpenTelemetry 采样比例: ${ratio}`;

  /** 构造不支持的采样器类型的错误消息 */
  static readonly OTEL_UNSUPPORTED_SAMPLER = (sampler: string): string =>
    `不支持的 OpenTelemetry 采样器: ${sampler}`;

  // ===== MongoDB 工具消息 =====

  // ===== MongoDB 与 SQL 代理 =====

  /** 构造 MongoDB 集合不在白名单的错误消息 */
  static readonly MONGO_COLLECTION_NOT_ALLOWED_MSG = (
    collectionName: string,
  ): string => `不允许查询集合: ${collectionName}`;

  /** 构造使用了禁用查询操作符的错误消息 */
  static readonly MONGO_FORBIDDEN_OPERATOR_MSG = (key: string): string =>
    `不允许使用操作符: ${key}`;

  /** 构造聚合管道阶段数超限的错误消息 */
  static readonly MONGO_AGGREGATE_PIPELINE_TOO_LONG_MSG = (
    max: number,
  ): string => `聚合管道阶段数不能超过 ${max}`;

  /** 构造聚合阶段结构不合法的错误消息 */
  static readonly MONGO_AGGREGATE_STAGE_SHAPE_INVALID_MSG = (
    position: number,
    stage: string,
  ): string =>
    `聚合管道第 ${position} 个阶段必须是只包含一个操作符的对象，实际收到: ${stage}`;

  /** 构造聚合阶段不在白名单的错误消息 */
  static readonly MONGO_AGGREGATE_STAGE_NOT_ALLOWED_MSG = (
    position: number,
    stage: string,
  ): string => `聚合管道第 ${position} 个阶段的阶段名 ${stage} 不受支持`;

  /** 构造聚合阶段取值不合法的错误消息 */
  static readonly MONGO_AGGREGATE_STAGE_VALUE_INVALID_MSG = (
    stage: string,
  ): string => `聚合阶段 ${stage} 的参数格式不正确`;

  /** 构造 SQL 代理表名不在白名单的错误消息 */
  static readonly SQL_PROXY_TABLE_NOT_ALLOWED = (tableName: string): string =>
    `安全限制：表 '${tableName}' 不在白名单内`;

  /** 构造 SQL 代理查询失败的错误消息 */
  static readonly SQL_PROXY_QUERY_FAILED = (message: string): string =>
    `执行SQL查询失败: ${message}`;

  /** 构造表结构查询失败的错误消息 */
  static readonly SQL_PROXY_TABLE_SCHEMA_FAILED = (message: string): string =>
    `获取表结构信息失败: ${message}`;

  /** 聚合管道为空的校验消息 */
  static readonly MONGO_AGGREGATE_PIPELINE_EMPTY = "聚合管道不能为空";

  // ===== 内部令牌短消息 =====

  /** 内部令牌密钥未配置的错误消息 */
  static readonly INTERNAL_TOKEN_SECRET_NOT_CONFIGURED = "内部令牌密钥未配置";

  /** 请求头缺少内部令牌的错误消息 */
  static readonly INTERNAL_TOKEN_MISSING = "请求头中缺少内部令牌";

  /** 内部令牌无效的错误消息 */
  static readonly INTERNAL_TOKEN_INVALID = "内部令牌无效";

  /** 内部令牌已过期的错误消息 */
  static readonly INTERNAL_TOKEN_EXPIRED = "内部令牌已过期";

  /** 内部令牌服务名不匹配的错误消息 */
  static readonly SERVICE_NAME_MISMATCH = "服务名称不匹配";

  // ===== RabbitMQ =====

  // ===== 消息消费 =====

  /** API 日志消息开始消费的日志消息 */
  static readonly API_RABBITMQ_START = "启动 ApiLog RabbitMQ 消息监听";

  /** API 日志已保存到数据库的日志消息 */
  static readonly API_SAVE = "API 日志已保存到数据库";

  /** 文章日志消息开始消费的日志消息 */
  static readonly ARTICLE_RABBITMQ_START = "启动 ArticleLog RabbitMQ 消息监听";

  /** 文章日志消息处理完成的日志消息 */
  static readonly ARTICLE_HANDLER = "ArticleLog 消息处理完成";

  /** 文章日志消息缺少 action 字段的提示 */
  static readonly ARTICLE_LESS_ACTION = "ArticleLog 消息缺少 action 字段";

  /** 文章日志消息缺少 content 字段的提示 */
  static readonly ARTICLE_LESS_CONTNET = "ArticleLog 消息缺少 content 字段";

  /** 文章日志写入成功的提示 */
  static readonly ARTICLE_SAVE = "ArticleLog 写入成功";

  // ===== 通用与兜底文案 =====

  /** 未传入文件路径的错误消息 */
  static readonly EMPTY_FILE_PATH = "未配置文件保存路径";

  /** RabbitMQ 连接成功的日志消息 */
  static readonly RABBITMQ_CONNECTION = "RabbitMQ连接成功";

  // ===== 定时任务 =====

  /** 定时任务开始清理超期 API 日志的日志消息 */
  static readonly TASK_CLEAN = "开始清理超过3个月的 API 日志";

  // ===== 通用错误消息 =====

  /** 未预期异常返回给调用方的兜底消息 */
  static readonly ERROR_DEFAULT_MSG = "NestJS服务器错误";

  /** 参数校验失败的提示 */
  static readonly PARAM_ERROR = "参数解析失败";

  /** 未授权用户的拒绝提示 */
  static readonly UNAUTHORIZED_USER = "未授权的用户，无法访问";

  /** 请求上下文缺少登录用户身份的错误消息 */
  static readonly USER_IDENTITY_MISSING = "请求上下文中缺少登录用户标识";

  /** 仅本人或管理员可访问的错误消息 */
  static readonly SELF_OR_ADMIN_REQUIRED =
    "仅允许访问本人数据，或需要管理员权限";

  /** 目标用户标识非法的错误消息 */
  static readonly USER_SCOPE_TARGET_INVALID = "目标用户标识必须为正整数";

  /** 当前用户没有管理员权限的提示 */
  static readonly NO_ADMIN_USER = "当前用户没有管理员权限，无法访问此功能";

  /** 用户名缺失时的占位名 */
  static readonly UNKNOWN_USERNAME = "unknown";

  /** 用户信息缺失时的兜底名称 */
  static readonly UNKNOWN_USER = "未知用户";

  /** 未知异常的兜底文案 */
  static readonly UNKNOWN_ERROR = "未知错误";

  /** 文章信息缺失时的兜底名称 */
  static readonly UNKNOWN_ARTICLE = "未知文章";

  // ===== 日志模块消息 =====

  /** 文章日志记录不存在的错误消息 */
  static readonly ARTICLE_LOG_NOT_FOUND = "文章日志记录不存在";

  /** 部分文章日志记录不存在的提示 */
  static readonly ARTICLE_LOG_PARTIAL_NOT_FOUND =
    "部分或全部文章日志记录不存在";

  /** API 日志记录不存在的错误消息 */
  static readonly API_LOG_NOT_FOUND = "API日志记录不存在";

  /** 部分或全部 API 日志记录不存在的提示 */
  static readonly API_LOG_PARTIAL_NOT_FOUND = "部分或全部API日志记录不存在";

  // ===== Nacos =====

  // ===== Nacos 注册消息 =====

  /** 注册到 Nacos 成功的日志消息 */
  static readonly REGISTER_NACOS = "注册到 nacos 成功";

  /** Nacos 服务地址未配置的错误消息 */
  static readonly NACOS_HOST_NOT_CONFIGURED = "Nacos 服务地址未配置";

  /** Nacos 服务端口未配置的错误消息 */
  static readonly NACOS_PORT_NOT_CONFIGURED = "Nacos 服务端口未配置";

  /** 服务运行模式未配置的错误消息 */
  static readonly SERVER_MODE_NOT_CONFIGURED = "服务运行模式未配置";

  /** 从 Nacos 注销实例成功的日志消息 */
  static readonly NACOS_DEREGISTER = "从 nacos 注销实例成功";

  /** 远程调用连接池已释放的日志消息 */
  static readonly REMOTE_CALL_AGENT_DESTROYED = "远程调用连接池已释放";

  // ===== GitHub 登录 =====

  // ===== GitHub 登录 =====

  /** GitHub 登录流程失败日志的固定前缀 */
  static readonly GITHUB_LOGIN_PROCESS_FAILED_PREFIX = "GitHub 登录处理失败: ";

  /** Redis 不可用导致无法完成 GitHub 登录的提示 */
  static readonly GITHUB_REDIS_UNAVAILABLE =
    "Redis 未配置，无法发起 GitHub 登录";

  /** GitHub 授权回调参数缺失的错误消息 */
  static readonly GITHUB_AUTH_PARAMS_MISSING = "GitHub 授权参数缺失";

  /** GitHub 授权取消或失败的错误消息 */
  static readonly GITHUB_AUTH_CANCELLED_OR_FAILED = "GitHub 授权已取消或失败";

  /** GitHub OAuth 配置不完整日志的固定前缀 */
  static readonly GITHUB_OAUTH_CONFIG_INCOMPLETE_PREFIX =
    "GitHub OAuth 配置不完整，缺少 ";

  /** Redis 不可用导致无法读取授权状态的错误消息 */
  static readonly GITHUB_REDIS_STATE_UNAVAILABLE =
    "Redis 未配置，无法处理 GitHub 登录状态";

  /** 授权状态过期的提示 */
  static readonly GITHUB_STATE_EXPIRED = "GitHub 授权状态已过期，请重新登录";

  /** 授权状态解析失败的错误消息 */
  static readonly GITHUB_STATE_PARSE_FAILED =
    "GitHub 授权状态解析失败，请重新登录";

  /** GitHub 访问令牌获取失败的提示 */
  static readonly GITHUB_ACCESS_TOKEN_FAILED = "GitHub 访问令牌获取失败";

  /** GitHub 用户资料获取失败的提示 */
  static readonly GITHUB_USER_PROFILE_FAILED = "GitHub 用户资料获取失败";

  /** GitHub 用户资料不完整的提示 */
  static readonly GITHUB_USER_PROFILE_INVALID = "GitHub 用户资料不完整";

  /** 响应缺少 id 或 login 字段的提示 */
  static readonly GITHUB_USER_PROFILE_MISSING_FIELDS = "响应缺少 id 或 login";

  /** 向 Spring 换取登录票据失败的提示 */
  static readonly GITHUB_SPRING_TOKEN_TICKET_FAILED =
    "Spring 未正确返回 GitHub 登录票据";

  /** Spring 未返回登录票据的提示 */
  static readonly GITHUB_SPRING_TOKEN_TICKET_MISSING =
    "Spring 未返回 GitHub 登录票据";

  // ===== 启动/测试 =====

  // ===== 启动与自检 =====

  /** 服务连通性测试返回的欢迎语 */
  static readonly TEST_WELCOME = "Hello,I am Nest.js!";

  /** 服务启动成功的提示 */
  static readonly START_WELCOME = "NestJS应用已启动";

  /** 服务启动失败的日志消息 */
  static readonly SERVER_START_FAILED = "NestJS 服务启动失败";

  // ===== OSS =====

  // ===== OSS 与文件 =====

  /** 上传失败落入 OSS 错误的日志消息 */
  static readonly OSS_UPLOAD_ERR = "上传阿里云OSS错误";

  /** OSS 配置不完整的错误消息 */
  static readonly OSS_CONFIG_INCOMPLETE =
    "OSS 配置不完整，请检查 application.yaml 中的 oss 配置";

  /** OSS put 操作开始的日志消息 */
  static readonly OSS_PUT_OPERATION_START = "开始执行 OSS put 操作...";

  /** OSS 上传失败的错误消息 */
  static readonly OSS_UPLOAD_FAILED = "OSS 上传失败";

  /** Bun 运行时下 OSS 兼容处理的提示 */
  static readonly OSS_BUN_RUNTIME_COMPAT_MESSAGE =
    "检测到 Bun 运行时，OSS 上传将使用兼容实现";

  /** OSS 客户端未初始化的错误消息 */
  static readonly OSS_CLIENT_NOT_INITIALIZED = "OSS 客户端尚未初始化";

  /** OSS put 操作超时的错误消息 */
  static readonly OSS_PUT_OPERATION_TIMEOUT = "OSS put 操作超时";

  /** OSS 返回非成功状态的日志前缀 */
  static readonly OSS_RESPONSE_NON_SUCCESS_PREFIX = "OSS 返回非成功状态码";

  /** OSS 响应正文的日志前缀 */
  static readonly OSS_RESPONSE_CONTENT_PREFIX = "响应内容:";

  // ===== 文件上传 =====

  /** 文件写入临时目录开始的日志消息 */
  static readonly FILE_SAVE_TEMP_START = "开始保存文件到临时目录...";

  /** 文件上传 OSS 开始的日志消息 */
  static readonly FILE_UPLOAD_OSS_START = "开始上传文件到 OSS...";

  /** 临时文件清理开始的日志消息 */
  static readonly FILE_CLEANUP_START = "开始清理临时文件...";

  /** 临时文件清理完成的日志消息 */
  static readonly FILE_CLEANUP_COMPLETED = "临时文件清理完成";

  /** 仅支持上传 PDF 的提示 */
  static readonly ONLY_PDF_SUPPORTED = "只支持上传 PDF 文件";

  /** 未上传文件的提示 */
  static readonly NO_FILE_UPLOADED = "未上传文件";

  /** 使用 toBuffer 读取文件的日志消息 */
  static readonly USING_TO_BUFFER_METHOD = "使用 toBuffer() 方法读取文件";

  /** 文件对象缺少可用读取方法的错误消息 */
  static readonly FILE_NO_VALID_METHOD =
    "文件对象既没有 file 属性也没有 toBuffer 方法";

  /** Word 文件保存路径未配置的错误消息 */
  static readonly WORD_FILE_PATH_NOT_CONFIGURED = "Word 文件保存路径未配置";

  /** 未找到文件分片的错误消息 */
  static readonly FILE_PART_NOT_FOUND = "未找到文件部分";

  // ===== 邮件 =====

  // ===== 邮件与验证码 =====

  /** 通用邮箱验证码邮件主题 */
  static readonly EMAIL_VERIFICATION_CODE_SUBJECT = "邮箱验证码";

  /** 注册验证码邮件主题 */
  static readonly EMAIL_VERIFICATION_CODE_REGISTER_SUBJECT = "注册验证码";

  /** 登录验证码邮件主题 */
  static readonly EMAIL_VERIFICATION_CODE_LOGIN_SUBJECT = "登录验证码";

  /** 重置密码验证码邮件主题 */
  static readonly EMAIL_VERIFICATION_CODE_RESET_SUBJECT = "重置密码验证码";

  /** 邮件服务配置不完整的错误消息 */
  static readonly MAIL_SERVICE_CONFIG_INCOMPLETE =
    "邮件 SMTP 配置不完整，邮件服务不可用";

  /** 邮件服务配置不正确的错误消息 */
  static readonly MAIL_SERVICE_CONFIG_INCORRECT =
    "邮件服务未正确配置，请检查 SMTP 配置";

  // ===== Redis 分布式锁消息 =====

  // ===== Redis 分布式锁 =====

  /** 分布式锁获取成功的日志消息 */
  static readonly REDIS_LOCK_ACQUIRE_SUCCESS = "获取分布式锁成功，key: %s";

  /** 分布式锁获取失败的日志消息 */
  static readonly REDIS_LOCK_ACQUIRE_FAIL =
    "获取分布式锁失败，跳过本次执行，key: %s";

  /** 分布式锁释放成功的日志消息 */
  static readonly REDIS_LOCK_RELEASE_SUCCESS = "释放分布式锁成功，key: %s";

  /** 分布式锁释放失败的日志消息 */
  static readonly REDIS_LOCK_RELEASE_FAIL = "释放分布式锁失败，key: %s";

  // ===== SQL 代理工具消息 =====

  // ===== SQL 代理校验 =====

  /** SQL 查询语句必须是字符串的校验消息 */
  static readonly SQL_PROXY_QUERY_MUST_BE_STRING = "SQL查询语句必须是字符串";

  /** SQL 查询语句不能为空的校验消息 */
  static readonly SQL_PROXY_QUERY_NOT_EMPTY = "SQL查询语句不能为空";

  /** SQL 命名参数必须是对象的校验消息 */
  static readonly SQL_PROXY_PARAMS_MUST_BE_OBJECT = "参数必须是对象";

  /** 命中禁用语句的校验消息 */
  static readonly SQL_PROXY_FORBIDDEN_STATEMENT =
    "安全限制：只允许执行只读查询（SELECT/WITH/SHOW/DESC/DESCRIBE/EXPLAIN）";

  /** 要求必须带 LIMIT 的校验消息 */
  static readonly SQL_PROXY_LIMIT_REQUIRED =
    "安全限制：SQL查询必须包含LIMIT子句";

  /** LIMIT 超过上限的校验消息 */
  static readonly SQL_PROXY_LIMIT_EXCEEDED = "安全限制：LIMIT超过最大限制100";

  /** 禁止执行多条 SQL 的校验消息 */
  static readonly SQL_PROXY_MULTIPLE_STATEMENTS =
    "安全限制：禁止执行多条SQL语句";
}
