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
   * 未知用户名
   */
  static readonly UNKNOWN_USER = '未知用户';

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
  static readonly SWAGGER_VERSION = '1.0';

  /**
   * Swagger 文档路径
   */
  static readonly SWAGGER_PATH = 'api-docs';

  /**
   * test 欢迎信息
   */
  static readonly TEST_WELCOME = 'Hello,I am Nest.js!';

  /**
   * 启动欢迎信息
   */
  static readonly START_WELCOME = 'NestJS应用已启动';
}
