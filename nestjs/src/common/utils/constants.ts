export class Constants {
  /**
   * 内部令牌密钥未配置
   */
  static readonly INTERNAL_TOKEN_SECRET_NOT_CONFIGURED = '内部令牌密钥未配置';

  /**
   * 内部令牌缺失
   */
  static readonly INTERNAL_TOKEN_MISSING = '请求头中缺少内部令牌';

  /**
   * 内部令牌无效
   */
  static readonly INTERNAL_TOKEN_INVALID = '内部令牌无效';

  /**
   * 内部令牌已过期
   */
  static readonly INTERNAL_TOKEN_EXPIRED = '内部令牌已过期';

  /**
   * 服务名称不匹配
   */
  static readonly SERVICE_NAME_MISMATCH = '服务名称不匹配';

  /**
   * 启动ApiLog RabbitMQ消息
   */
  static readonly API_RABBITMQ_START = '启动 ApiLog RabbitMQ 消息监听';

  /**
   * API保存消息
   */
  static readonly API_SAVE = 'API 日志已保存到数据库';

  /**
   * 启动ArticleLog RabbitMQ消息
   */
  static readonly ARTICLE_RABBITMQ_START = '启动 ArticleLog RabbitMQ 消息监听';

  /**
   * Article消息处理完成消息
   */
  static readonly ARTICLE_HANDLER = 'ArticleLog 消息处理完成';

  /**
   * Article日志缺少action字段
   */
  static readonly ARTICLE_LESS_ACTION = 'ArticleLog 消息缺少 action 字段';

  /**
   * Article日志缺少content字段
   */
  static readonly ARTICLE_LESS_CONTNET = 'ArticleLog 消息缺少 content 字段';

  /**
   * Article保存消息
   */
  static readonly ARTICLE_SAVE = 'ArticleLog 写入成功';

  /**
   * 未配置文件路径消息
   */
  static readonly EMPTY_FILE_PATH = '未配置文件保存路径';

  /**
   * RabbitMQ连接成功消息
   */
  static readonly RABBITMQ_CONNECTION = 'RabbitMQ连接成功';

  /**
   * 清理日志定时任务消息
   */
  static readonly TASK_CLEAN = '开始清理超过1个月的 API 日志';

  /**
   * 清理文章日志定时任务消息
   */
  static readonly TASK_ARTICLE_CLEAN = '开始清理超过1个月的文章日志';

  /**
   * 服务器错误消息
   */
  static readonly ERROR_DEFAULT_MSG = 'NestJS服务器错误';

  /**
   * 参数解析错误消息
   */
  static readonly PARAM_ERROR = '参数解析失败';

  /**
   * 未授权用户访问错误消息
   */
  static readonly UNAUTHORIZED_USER = '未授权的用户，无法访问';

  /**
   * 非管理员用户访问错误消息
   */
  static readonly NO_ADMIN_USER = '当前用户没有管理员权限，无法访问此功能';

  /**
   * 阿里云OSS上传错误消息
   */
  static readonly OSS_UPLOAD_ERR = '上传阿里云OSS错误';

  /**
   * 未知用户名
   */
  static readonly UNKNOWN_USERNAME = 'unknown';

  /**
   * 文章日志记录不存在消息
   */
  static readonly ARTICLE_LOG_NOT_FOUND = '文章日志记录不存在';

  /**
   * 部分或全部文章日志记录不存在消息
   */
  static readonly ARTICLE_LOG_PARTIAL_NOT_FOUND =
    '部分或全部文章日志记录不存在';

  /**
   * API日志记录不存在消息
   */
  static readonly API_LOG_NOT_FOUND = 'API日志记录不存在';

  /**
   * 部分或全部API日志记录不存在消息
   */
  static readonly API_LOG_PARTIAL_NOT_FOUND = '部分或全部API日志记录不存在';

  /**
   * 注册Nacos成功消息
   */
  static readonly REGISTER_NACOS = '注册到 nacos 成功';

  /**
   * dev 模式下 Nacos 注册消息
   */
  static readonly REGISTER_NACOS_DEV_MODE =
    'SERVER_MODE=dev，Nacos 注册统一使用 127.0.0.1';

  /**
   * Nacos 服务地址未配置
   */
  static readonly NACOS_HOST_NOT_CONFIGURED = 'Nacos 服务地址未配置';

  /**
   * Nacos 服务端口未配置
   */
  static readonly NACOS_PORT_NOT_CONFIGURED = 'Nacos 服务端口未配置';

  /**
   * 服务运行模式未配置
   */
  static readonly SERVER_MODE_NOT_CONFIGURED = '服务运行模式未配置';

  /**
   * 未知用户名
   */
  static readonly UNKNOWN_USER = '未知用户';

  /**
   * GitHub 登录处理失败前缀
   */
  static readonly GITHUB_LOGIN_PROCESS_FAILED_PREFIX = 'GitHub 登录处理失败: ';

  /**
   * GitHub 登录 Redis 未配置消息
   */
  static readonly GITHUB_REDIS_UNAVAILABLE =
    'Redis 未配置，无法发起 GitHub 登录';

  /**
   * GitHub 授权参数缺失消息
   */
  static readonly GITHUB_AUTH_PARAMS_MISSING = 'GitHub 授权参数缺失';

  /**
   * GitHub 授权已取消或失败消息
   */
  static readonly GITHUB_AUTH_CANCELLED_OR_FAILED = 'GitHub 授权已取消或失败';

  /**
   * GitHub OAuth 配置不完整前缀
   */
  static readonly GITHUB_OAUTH_CONFIG_INCOMPLETE_PREFIX =
    'GitHub OAuth 配置不完整，缺少 ';

  /**
   * GitHub 登录状态 Redis 未配置消息
   */
  static readonly GITHUB_REDIS_STATE_UNAVAILABLE =
    'Redis 未配置，无法处理 GitHub 登录状态';

  /**
   * GitHub 授权状态已过期消息
   */
  static readonly GITHUB_STATE_EXPIRED = 'GitHub 授权状态已过期，请重新登录';

  /**
   * GitHub 授权状态解析失败消息
   */
  static readonly GITHUB_STATE_PARSE_FAILED =
    'GitHub 授权状态解析失败，请重新登录';

  /**
   * GitHub 访问令牌获取失败消息
   */
  static readonly GITHUB_ACCESS_TOKEN_FAILED = 'GitHub 访问令牌获取失败';

  /**
   * GitHub 用户资料获取失败消息
   */
  static readonly GITHUB_USER_PROFILE_FAILED = 'GitHub 用户资料获取失败';

  /**
   * GitHub 用户资料不完整消息
   */
  static readonly GITHUB_USER_PROFILE_INVALID = 'GitHub 用户资料不完整';

  /**
   * Spring 未正确返回 GitHub 登录票据消息
   */
  static readonly GITHUB_SPRING_TOKEN_TICKET_FAILED =
    'Spring 未正确返回 GitHub 登录票据';

  /**
   * Spring 未返回 GitHub 登录票据消息
   */
  static readonly GITHUB_SPRING_TOKEN_TICKET_MISSING =
    'Spring 未返回 GitHub 登录票据';

  /**
   * 通用未知错误
   */
  static readonly UNKNOWN_ERROR = '未知错误';

  /**
   * 熔断器打开消息
   */
  static readonly CIRCUIT_BREAKER_OPEN = '熔断器已打开';

  // Swagger 相关常量

  /**
   * Swagger 标题
   */
  static readonly SWAGGER_TITLE = 'NestJS部分的Swagger文档';

  /**
   * Swagger 描述
   */
  static readonly SWAGGER_DESCRIPTION = '这是项目的NestJS部分的Swagger文档';

  /**
   * Swagger 版本
   */
  static readonly SWAGGER_VERSION = '1.0.0';

  /**
   * Swagger 文档路径
   */
  static readonly SWAGGER_PATH = 'api-docs';

  /**
   * Swagger 标签描述
   */
  static readonly SWAGGER_TAGS: [string, string][] = [
    ['API日志模块', 'API日志相关API，包括日志查询、统计等功能'],
    ['文章日志模块', '文章操作日志相关API，包括日志记录、查询、清理等'],
    ['测试模块', '服务测试相关API，用于验证各个微服务是否正常运行'],
    ['文件上传', '文件上传相关API，包括本地文件上传、图片上传、PDF上传等'],
    ['下载模块', '文件下载相关API，包括Word下载、PDF下载等'],
    [
      'GitHub 登录模块',
      'GitHub 授权与操作相关API，包括授权登录、用户信息获取等',
    ],
    ['邮件模块', '邮件发送相关API，包括验证码邮件、通知邮件等'],
  ];

  /**
   * test 欢迎信息
   */
  static readonly TEST_WELCOME = 'Hello,I am Nest.js!';

  /**
   * 启动欢迎信息
   */
  static readonly START_WELCOME = 'NestJS应用已启动';

  /**
   * 初始IP地址
   */
  static readonly INIT_IP = '127.0.0.1';

  // OSS 相关常量

  /**
   * OSS 配置不完整错误消息
   */
  static readonly OSS_CONFIG_INCOMPLETE =
    'OSS 配置不完整，请检查 application.yaml 中的 oss 配置';

  /**
   * 开始执行 OSS put 操作消息
   */
  static readonly OSS_PUT_OPERATION_START = '开始执行 OSS put 操作...';

  /**
   * OSS 上传失败消息
   */
  static readonly OSS_UPLOAD_FAILED = 'OSS 上传失败';

  /**
   * 检测到 Bun 运行时消息
   */
  static readonly OSS_BUN_RUNTIME_COMPAT_MESSAGE =
    '检测到 Bun 运行时，OSS 上传将使用兼容实现';

  /**
   * OSS 客户端未初始化消息
   */
  static readonly OSS_CLIENT_NOT_INITIALIZED = 'OSS 客户端尚未初始化';

  /**
   * OSS 上传超时消息
   */
  static readonly OSS_PUT_OPERATION_TIMEOUT = 'OSS put 操作超时';

  /**
   * OSS 返回非成功状态码前缀
   */
  static readonly OSS_RESPONSE_NON_SUCCESS_PREFIX = 'OSS 返回非成功状态码';

  /**
   * OSS 响应内容前缀
   */
  static readonly OSS_RESPONSE_CONTENT_PREFIX = '响应内容:';

  /**
   * OSS HTTP 方法
   */
  static readonly OSS_HTTP_PUT_METHOD = 'PUT';

  /**
   * OSS 默认上传内容类型
   */
  static readonly OSS_DEFAULT_CONTENT_TYPE = 'application/octet-stream';

  // 文件上传相关常量

  /**
   * 开始保存文件到临时目录消息
   */
  static readonly FILE_SAVE_TEMP_START = '开始保存文件到临时目录...';

  /**
   * 开始上传文件到 OSS 消息
   */
  static readonly FILE_UPLOAD_OSS_START = '开始上传文件到 OSS...';

  /**
   * 开始清理临时文件消息
   */
  static readonly FILE_CLEANUP_START = '开始清理临时文件...';

  /**
   * 临时文件清理完成消息
   */
  static readonly FILE_CLEANUP_COMPLETED = '临时文件清理完成';

  /**
   * 仅支持上传 PDF 文件错误消息
   */
  static readonly ONLY_PDF_SUPPORTED = '只支持上传 PDF 文件';

  /**
   * 未上传文件错误消息
   */
  static readonly NO_FILE_UPLOADED = '未上传文件';

  /**
   * 使用 toBuffer 方法读取文件消息
   */
  static readonly USING_TO_BUFFER_METHOD = '使用 toBuffer() 方法读取文件';

  /**
   * 文件对象既没有 file 属性也没有 toBuffer 方法错误消息
   */
  static readonly FILE_NO_VALID_METHOD =
    '文件对象既没有 file 属性也没有 toBuffer 方法';

  /**
   * Word 文件保存路径未配置
   */
  static readonly WORD_FILE_PATH_NOT_CONFIGURED = 'Word 文件保存路径未配置';

  /**
   * 未找到文件部分错误消息
   */
  static readonly FILE_PART_NOT_FOUND = '未找到文件部分';

  // 邮件相关常量

  /**
   * 邮箱验证码标题
   */
  static readonly EMAIL_VERIFICATION_CODE_SUBJECT = '邮箱验证码';

  /**
   * 注册验证码标题
   */
  static readonly EMAIL_VERIFICATION_CODE_REGISTER_SUBJECT = '注册验证码';

  /**
   * 登录验证码标题
   */
  static readonly EMAIL_VERIFICATION_CODE_LOGIN_SUBJECT = '登录验证码';

  /**
   * 重置密码验证码标题
   */
  static readonly EMAIL_VERIFICATION_CODE_RESET_SUBJECT = '重置密码验证码';

  /**
   * 邮件服务配置不完整错误消息
   */
  static readonly MAIL_SERVICE_CONFIG_INCOMPLETE =
    '邮件 SMTP 配置不完整，邮件服务不可用';

  /**
   * 邮件服务未正确配置错误消息
   */
  static readonly MAIL_SERVICE_CONFIG_INCORRECT =
    '邮件服务未正确配置，请检查 SMTP 配置';

  /**
   * 验证码邮件发送失败错误消息
   */
  static readonly EMAIL_VERIFICATION_CODE_SEND_FAILED = '验证码邮件发送失败';
  // Redis 相关常量

  /**
   * Redis 客户端注入 token
   */
  static readonly REDIS_CLIENT = 'REDIS_CLIENT';

  // Redis 分布式锁相关常量

  /**
   * API日志清理任务分布式锁的 key
   */
  static readonly LOCK_TASK_API_LOG_CLEANUP = 'lock:task:api:log:cleanup';

  /**
   * API日志清理任务分布式锁的过期时间（秒）
   */
  static readonly LOCK_TASK_API_LOG_CLEANUP_EXPIRE = 3600;

  /**
   * 文章日志清理任务分布式锁的 key
   */
  static readonly LOCK_TASK_ARTICLE_LOG_CLEANUP =
    'lock:task:article:log:cleanup';

  /**
   * 文章日志清理任务分布式锁的过期时间（秒）
   */
  static readonly LOCK_TASK_ARTICLE_LOG_CLEANUP_EXPIRE = 3600;

  /**
   * 获取分布式锁成功消息
   */
  static readonly REDIS_LOCK_ACQUIRE_SUCCESS = '获取分布式锁成功，key: %s';

  /**
   * 获取分布式锁失败消息（其他实例正在执行）
   */
  static readonly REDIS_LOCK_ACQUIRE_FAIL =
    '获取分布式锁失败，跳过本次执行，key: %s';

  /**
   * 释放分布式锁成功消息
   */
  static readonly REDIS_LOCK_RELEASE_SUCCESS = '释放分布式锁成功，key: %s';

  /**
   * 释放分布式锁失败消息（锁已过期或被其他实例持有）
   */
  static readonly REDIS_LOCK_RELEASE_FAIL = '释放分布式锁失败，key: %s';

  // Redis Lua 脚本

  /**
   * 解锁 Lua 脚本：只有当锁的值与预期值一致时才删除，保证只有锁持有者才能解锁
   */
  static readonly UNLOCK_SCRIPT = `
    if redis.call("get", KEYS[1]) == ARGV[1] then
      return redis.call("del", KEYS[1])
    else
      return 0
    end
  `;

  // 错误标识常量

  // 400 Bad Request
  static readonly PARAM_PARSE_FAILED = 'PARAM_PARSE_FAILED';

  // 403 Forbidden
  static readonly UNAUTHORIZED_USER_ERROR = 'UNAUTHORIZED_USER';
  static readonly NO_ADMIN_PERMISSION = 'NO_ADMIN_PERMISSION';
  static readonly INTERNAL_TOKEN_SERVICE_MISMATCH =
    'INTERNAL_TOKEN_SERVICE_MISMATCH';

  // 404 Not Found
  static readonly ARTICLE_LOG_NOT_FOUND_ERROR = 'ARTICLE_LOG_NOT_FOUND';
  static readonly ARTICLE_LOG_PARTIAL_NOT_FOUND_ERROR =
    'ARTICLE_LOG_PARTIAL_NOT_FOUND';
  static readonly API_LOG_NOT_FOUND_ERROR = 'API_LOG_NOT_FOUND';
  static readonly API_LOG_PARTIAL_NOT_FOUND_ERROR = 'API_LOG_PARTIAL_NOT_FOUND';
  static readonly FILE_PART_NOT_FOUND_ERROR = 'FILE_PART_NOT_FOUND';

  // 401 Unauthorized
  static readonly INTERNAL_TOKEN_MISSING_ERROR = 'INTERNAL_TOKEN_MISSING';
  static readonly INTERNAL_TOKEN_INVALID_ERROR = 'INTERNAL_TOKEN_INVALID';
  static readonly INTERNAL_TOKEN_EXPIRED_ERROR = 'INTERNAL_TOKEN_EXPIRED';

  // 422 Unprocessable Entity
  static readonly ONLY_PDF_SUPPORTED_ERROR = 'ONLY_PDF_SUPPORTED';
  static readonly NO_FILE_UPLOADED_ERROR = 'NO_FILE_UPLOADED';
  static readonly FILE_NO_VALID_METHOD_ERROR = 'FILE_NO_VALID_METHOD';

  // 500 Internal Server Error
  static readonly NESTJS_SERVER_ERROR = 'NESTJS_SERVER_ERROR';
  static readonly OSS_UPLOAD_ERROR = 'OSS_UPLOAD_ERROR';

  // 503 Service Unavailable
  static readonly OSS_CLIENT_NOT_INITIALIZED_ERROR =
    'OSS_CLIENT_NOT_INITIALIZED';
  static readonly SERVICE_DISCOVERY_FAILED = 'SERVICE_DISCOVERY_FAILED';
  static readonly NO_AVAILABLE_SERVICE_INSTANCE =
    'NO_AVAILABLE_SERVICE_INSTANCE';

  // 504 Gateway Timeout
  static readonly OSS_PUT_TIMEOUT = 'OSS_PUT_TIMEOUT';

  // 502 Bad Gateway
  static readonly SERVICE_CALL_FAILED = 'SERVICE_CALL_FAILED';
}
