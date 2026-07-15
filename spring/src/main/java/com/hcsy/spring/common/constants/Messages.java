package com.hcsy.spring.common.constants;

/**
 * 消息类常量 — 日志消息、用户提示、状态描述
 */
public class Messages {

    private Messages() {}

    // ===== 错误信息 =====
    public static final String COLLECT_FAIL = "收藏失败，可能已经收藏过了";
    public static final String UNCOLLECT_FAIL = "取消收藏失败，记录不存在";
    public static final String LIKE_FAIL = "点赞失败，可能已经点过赞了";
    public static final String UNLIKE_FAIL = "取消点赞失败，记录不存在";
    public static final String FOCUS_FAIL = "关注失败，可能已经关注过了";
    public static final String UNFOCUS_FAIL = "取消关注失败，记录不存在";

    // ===== 实体不存在 =====
    public static final String UNDEFINED_USER = "用户不存在";
    public static final String UNDEFINED_SUB_CATEGORY_ID = "子分类ID不能为空";
    public static final String UNDEFINED_SUB_CATEGORY = "子分类不存在";
    public static final String UNDEFINED_ARTICLE = "文章不存在";
    public static final String UNDEFINED_CATEGORY = "分类不存在";
    public static final String UNDEFINED_ARTICLE_COMMENT = "文章不存在，无法评论";
    public static final String UNDEFINED_USER_COMMENT = "用户不存在，无法评论";
    public static final String UNDEFINED_ARTICLES = "部分或全部文章不存在";
    public static final String UNDEFINED_USERS = "部分或全部用户不存在";
    public static final String UNDEFINED_CATEGORIES = "部分或全部分类不存在";
    public static final String UNDEFINED_SUB_CATEGORIES = "部分或全部子分类不存在";
    public static final String UNDEFINED_COMMENTS = "部分或全部评论不存在";
    public static final String SORT_WAY = "不支持的排序方式: ";

    // ===== 登录/验证码 =====
    public static final String LOGIN = "用户名或密码错误";
    public static final String VERIFY_CODE = "邮箱验证码无效或已过期";
    public static final String IMAGE_CAPTCHA_INVALID = "图形验证码错误或已过期";
    public static final String UNDEFINED_USER_REGISTER = "用户不存在，请先注册";
    public static final String EMAIL_REGISTER = "邮箱已被注册";
    public static final String EMAIL_UNREGISTER = "邮箱未注册，请先注册";
    public static final String VERIFY_CODE_UNSUPPORT = "不支持的类型，请使用 register、login 或 reset";
    public static final String EMAIL = "邮箱格式不正确";
    public static final String PASSWORD_NO_USER = "没有用户可重置";

    // ===== GitHub 登录 =====
    public static final String GITHUB_ACCOUNT_PASSWORD_LOGIN_BLOCKED = "该账号通过 GitHub 登录创建，请使用 GitHub 登录或先设置密码";
    public static final String GITHUB_LOGIN_TICKET_CACHE_FAILED = "缓存 GitHub 登录票据失败";
    public static final String GITHUB_TOKEN_TICKET_EMPTY = "GitHub 登录票据不能为空";
    public static final String GITHUB_TOKEN_TICKET_EXPIRED = "GitHub 登录票据已过期，请重新登录";
    public static final String GITHUB_TOKEN_TICKET_PARSE_FAILED = "解析 GitHub 登录票据失败";
    public static final String GITHUB_TOKEN_TICKET_USER_ID_REQUIRED = "用户ID不能为空";
    public static final String GITHUB_TOKEN_TICKET_USERNAME_REQUIRED = "用户名不能为空";
    public static final String GITHUB_TOKEN_EXCHANGE_TICKET_REQUIRED = "票据不能为空";

    // ===== 文章发布/阅读量 =====
    public static final String UNDEFINED_ARTICLE_ID = "文章不存在，ID：";
    public static final String UNDEFINED_ARTICLE_ID_AUTHOR_ID = "文章作者ID为空，文章ID：";
    public static final String UNDEFINED_ARTICLE_AUTHOR_ID = "文章作者不存在，ID：";
    public static final String UNDEFINED_SUB_CATEGORY_ID_AUTHOR_ID = "文章子分类ID为空，文章ID：";
    public static final String UNDEFINED_SUB_CATEGORY_AUTHOR_ID = "文章子分类不存在，ID：";
    public static final String UNDEFINED_CATEGORY_ID_AUTHOR_ID = "文章子分类的父分类ID为空，子分类ID：";
    public static final String UNDEFINED_CATEGORY_AUTHOR_ID = "文章子分类的父分类不存在，ID：";
    public static final String PUBLISH_ARTICLE = "发布失败：文章不存在或更新失败";
    public static final String UNPUBLISH_ADD_VIEW = "文章未发布，无法增加阅读量";
    public static final String ADD_VIEW_ARTICLE = "增加阅读量失败：文章不存在或更新失败";

    // ===== ES/Vector/Neo4j 同步 =====
    public static final String SYNC = "触发同步 ES 和 Vector...";
    public static final String SYNC_ES_SUCCESS = "ES 同步完成";
    public static final String SYNC_ES_FAIL = "ES 同步失败: ";
    public static final String SYNC_VECTOR_SUCCESS = "Vector 同步完成";
    public static final String SYNC_VECTOR_FAIL = "Vector 同步失败: ";
    public static final String SYNC_ALL_SUCCESS = "所有同步任务执行完毕";
    public static final String SYNC_ALL_FAIL = "同步过程发生未知异常: ";
    public static final String SYNC_PARALLEL_SUCCESS = "%s 并行同步完成，总耗时: %dms";
    public static final String SYNC_PARALLEL_FAIL = "%s 并行同步失败，耗时: %dms, 错误: %s";
    public static final String SYNC_ES_DURATION = "ES 同步成功，耗时: %dms";
    public static final String SYNC_ES_RETRY = "ES 同步失败，第 %d 次重试，错误: %s";
    public static final String SYNC_ES_MAX_RETRY = "ES 同步失败，已达到最大重试次数: %s";
    public static final String SYNC_ES_RETRY_INTERRUPTED = "ES 同步重试被中断";
    public static final String SYNC_ES_FAILED = "ES 同步失败";
    public static final String SYNC_VECTOR_DURATION = "Vector 同步成功，耗时: %dms";
    public static final String SYNC_VECTOR_RETRY = "Vector 同步失败，第 %d 次重试，错误: %s";
    public static final String SYNC_VECTOR_MAX_RETRY = "Vector 同步失败，已达到最大重试次数: %s";
    public static final String SYNC_VECTOR_RETRY_INTERRUPTED = "Vector 同步重试被中断";
    public static final String SYNC_VECTOR_FAILED = "Vector 同步失败";
    public static final String SYNC_NEO4J_DURATION = "Neo4j 同步成功，耗时: %dms";
    public static final String SYNC_NEO4J_SUCCESS = "Neo4j 同步完成";
    public static final String SYNC_NEO4J_RETRY = "Neo4j 同步失败，第 %d 次重试，错误: %s";
    public static final String SYNC_NEO4J_MAX_RETRY = "Neo4j 同步失败，已达到最大重试次数: %s";
    public static final String SYNC_NEO4J_RETRY_INTERRUPTED = "Neo4j 同步重试被中断";
    public static final String SYNC_NEO4J_FAILED = "Neo4j 同步失败";

    // ===== Neo4j 同步任务描述 =====
    public static final String NEO4J_SYNC_TASK_START_MESSAGE = "Neo4j 同步任务开始执行，方法: %s，操作: %s";
    public static final String NEO4J_SYNC_TASK_SUBMIT_SUCCESS_MESSAGE = "Neo4j 同步异步任务已提交，方法: %s，操作: %s";
    public static final String NEO4J_SYNC_TASK_SUBMIT_FAIL_MESSAGE = "Neo4j 同步异步任务提交失败，方法: %s，操作: %s，错误: %s";
    public static final String NEO4J_SYNC_CALL_FAIL_MESSAGE = "Neo4j 同步调用失败，方法: %s，操作: %s，返回信息: %s";
    public static final String NEO4J_SYNC_CALL_EMPTY_MESSAGE = "Neo4j 同步调用返回空结果，方法: %s，操作: %s";
    public static final String NEO4J_SYNC_DESC_USER_SAVE = "保存用户后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_USER_DELETE = "删除用户后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_USER_BATCH_DELETE = "批量删除用户后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_USER_UPDATE = "修改用户后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_COMMENT_CREATE = "新增评论后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_COMMENT_UPDATE = "修改评论后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_COMMENT_DELETE = "删除评论后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_COMMENT_BATCH_DELETE = "批量删除评论后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_CATEGORY_CREATE = "新增分类后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_CATEGORY_UPDATE = "修改分类后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_CATEGORY_DELETE = "删除分类后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_CATEGORY_BATCH_DELETE = "批量删除分类后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_SUBCATEGORY_CREATE = "新增子分类后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_SUBCATEGORY_UPDATE = "修改子分类后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_SUBCATEGORY_DELETE = "删除子分类后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_SUBCATEGORY_BATCH_DELETE = "批量删除子分类后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_ARTICLE_CREATE = "新增文章后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_ARTICLE_UPDATE = "编辑文章后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_ARTICLE_DELETE = "删除文章后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_ARTICLE_BATCH_DELETE = "批量删除文章后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_ARTICLE_PUBLISH = "发布文章后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_ARTICLE_VIEW = "浏览文章后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_LIKE = "点赞文章后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_UNLIKE = "取消点赞文章后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_COLLECT = "收藏文章后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_UNCOLLECT = "取消收藏文章后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_FOCUS = "关注用户后同步 Neo4j";
    public static final String NEO4J_SYNC_DESC_UNFOCUS = "取消关注用户后同步 Neo4j";

    // ===== 缓存清理 =====
    public static final String CACHE_CLEAR_DURATION = "缓存清理成功，耗时: %dms";
    public static final String CACHE_CLEAR_RETRY = "缓存清理失败，第 %d 次重试，错误: %s";
    public static final String CACHE_CLEAR_MAX_RETRY = "缓存清理失败，已达到最大重试次数: %s";
    public static final String CACHE_CLEAR_RETRY_INTERRUPTED = "缓存清理重试被中断";
    public static final String CACHE_CLEAR_FAILED = "缓存清理失败";
    public static final String CLEAN_CONTEXT = "UserContext 已清理";
    public static final String CATEGORY_CACHE = "缓存未命中，从数据库加载 category";
    public static final String CATEGORY_CACHE_PAGE = "缓存未命中，从数据库加载分页数据";
    public static final String CLEAR_CACHE_SUCCESS = "成功清除分析相关缓存";
    public static final String CLEAR_CACHE_FAIL = "清除分析相关缓存失败: ";
    public static final String REFERENCE_EXIST = "该子分类已存在权威参考文本";
    public static final String PDF_EMPTY = "PDF类型必须提供pdf链接";
    public static final String LINK_EMPTY = "link类型必须提供link链接";
    public static final String PDF_TAIL = "PDF链接必须以.pdf结尾";

    // ===== 验证码 =====
    public static final String CODE_SAVE = "验证码已保存到 Redis: ";
    public static final String EMAIL_CODE = "邮箱验证码";
    public static final String CODE_SUCCESS = "验证码邮件已成功发送到: ";
    public static final String CODE_FAIL = "邮件发送失败 (MessagingException): ";
    public static final String CODE_EXCEPTION = "邮件发送异常: ";
    public static final String CODE_DELETE = "已删除过期的验证码: ";
    public static final String CODE_EXPIRED = "验证码已过期或不存在: ";
    public static final String CODE_VERIFY_FAIL = "验证码验证错误: ";
    public static final String CODE_VERIFY_SUCCESS = "邮箱验证成功: ";
    public static final String CODE_VERIFY_EXCEPTION = "验证码验证失败: ";
    public static final String IMAGE_CAPTCHA_SAVE = "图形验证码已保存到 Redis: ";
    public static final String IMAGE_CAPTCHA_DELETE = "图形验证码已删除: ";
    public static final String IMAGE_CAPTCHA_EXPIRED = "图形验证码已过期或不存在: ";
    public static final String IMAGE_CAPTCHA_VERIFY_FAIL = "图形验证码校验失败: ";
    public static final String IMAGE_CAPTCHA_VERIFY_SUCCESS = "图形验证码校验成功: ";
    public static final String IMAGE_CAPTCHA_GENERATE_FAIL = "图形验证码生成失败";

    // ===== JWT/Token =====
    public static final String LOGIN_TOKEN = "用户 %d 登录，Token 已保存到 Redis";
    public static final String REMOVE_TOKEN_LOGOUT = "用户 %d 没有其他登录会话，状态已设为离线";
    public static final String REMOVE_TOKEN = "用户 %d 登出，还有 %d 个登录会话";
    public static final String TOKEN_REDIS = "用户 %d 的 Token 不在 Redis 列表中，可能已被管理员踢下线";
    public static final String TOKEN_EXPIRED_CLEAN = "用户 %d 的 Token 已过期或格式错误，将从 Redis 列表中移除";
    public static final String VERIFY_TOKEN = "验证用户 %d 的 Token 时出错";
    public static final String ADMIN_TOKEN_CLEAN = "管理员已将用户 %d 下线，共清除 %d 个登录会话";
    public static final String TASK_NO_CLEAN = "定时任务：没有需要清理的 Token";
    public static final String REMOVE_EXPIRED_TOKEN = "移除过期 Token: %s";
    public static final String REMOVE_INVALID_TOKEN = "移除过期 Token: %s";
    public static final String NO_TOKEN_LOGOUT = "用户 %d 没有有效 Token，已标记为离线";
    public static final String EXPIRED_USER_FAIL = "解析用户 ID 失败: %s";
    public static final String USER_TOKEN_CLEAN = "用户 %s 清理了 %d 个 Token";
    public static final String TOTAL_CLEAN = "定时任务：清理完成，扫描 %d 个用户，共清除 %d 个过期 Token";
    public static final String JWT_NOT_NULL = "JWT 密钥不能为 null 或者为空";
    public static final String JWT_INIT = "JWT 密钥初始化完成";
    public static final String TOKEN_VERIFY_SUCCESS = "Token验证成功";
    public static final String TOKEN_EXPIRED = "Token已过期";
    public static final String UNUSED_TOKEN = "无效的Token";
    public static final String TOKEN_TYPE_INVALID = "Token类型错误，请使用正确的Token";
    public static final String REFRESH_TOKEN_INVALID = "Refresh Token 无效或已过期";
    public static final String REFRESH_TOKEN_SUCCESS = "Token 刷新成功";
    public static final String GET_USER_TOKEN_ID = "无法获取用户信息，请确保已登录";
    public static final String TOKEN_GEN_FAIL = "令牌生成失败";
    public static final String SESSION_NOT_FOUND = "登录会话不存在，请重新登录";
    public static final String LOGIN_SESSION_CREATED = "用户 %d 登录，创建会话 %s";
    public static final String LOGIN_SESSION_REMOVED = "用户 %d 登出，移除会话 %s";
    public static final String REMOVE_SESSION_LOGOUT = "用户 %d 没有其他登录会话，状态已设为离线";
    public static final String REMOVE_SESSION = "用户 %d 登出，还有 %d 个登录会话";
    public static final String TOKEN_ACCESS_REDIS = "用户 %d 的 Access Token 不在 Redis 中，可能已被踢下线";
    public static final String ADMIN_SESSION_CLEAN = "管理员已将用户 %d 下线，共清除 %d 个登录会话";
    public static final String TASK_NO_CLEAN_SESSION = "定时任务：没有需要清理的 Session";
    public static final String REMOVE_EXPIRED_REFRESH = "移除过期的 Refresh Token 关联的 Session: ";
    public static final String SESSION_CLEAN_LOG = "用户 %s 清理了 %d 个 Session";
    public static final String TOTAL_SESSION_CLEAN = "定时任务：清理完成，扫描 %d 个用户，共清除 %d 个过期 Session";

    // ===== AOP/权限 =====
    public static final String API_EXCEPTION = "API方法执行异常";
    public static final String TIME_FAIL = "记录执行时间失败";
    public static final String PARAM_EXPIRED = "参数解析失败";
    public static final String FORMAT_PARAM = "格式化参数值失败";
    public static final String OBJECT_TO_MAP = "对象转Map失败";
    public static final String PATH_PARAM = "提取路径参数失败";
    public static final String BODY_PARAM = "提取请求体失败";
    public static final String TRIGGER_SYNC = "事务提交后触发异步同步任务";
    public static final String UNSYNC_TYPE = "点赞/收藏/关注类操作不同步";
    public static final String TRANSACTION_ROLLBACK = "事务执行失败，已回滚";
    public static final String UNKNOWN_OPERATION = "AOP识别失败：未知的操作类型";
    public static final String UNLOGIN_DEFAULT = "用户未登录，使用默认用户ID: -1";
    public static final String ADMIN_PASS = "用户具有管理员权限，直接通过";
    public static final String TARGET_SOURCE = "当前用户ID: %d, 业务类型: %s, 参数来源: %s, 目标资源ID: %s";
    public static final String NO_PERMISION = "权限不足，无法执行此操作";
    public static final String PERMITION_FAIL = "权限检查失败";
    public static final String TARGET_FAIL = "获取目标资源ID失败: ";
    public static final String FUNCTION_PATH = "从方法参数获取路径参数 %s = %d";
    public static final String FUNCTION_PATH_FAIL = "路径参数转换失败: ";
    public static final String URL_ID = "从URL路径获取ID: %d";
    public static final String URL_ID_FAIL = "URL最后一个路径段不是数字: %s";
    public static final String SINGLE_PATH = "获取路径单个参数失败: ";
    public static final String COMMENT_ID = "评论ID不存在: ";
    public static final String COMMENT_NO_USER = "评论ID未关联用户: ";
    public static final String COMMENT_MULTI_USER = "批量删除的评论属于不同用户";
    public static final String FUNCTION_COMMENT = "从方法参数获取批量评论用户ID: %d";
    public static final String ARTICLE_ID = "文章ID不存在: ";
    public static final String ARTICLE_NO_USER = "文章ID未关联用户: ";
    public static final String ARTICLE_MULTI_USER = "批量删除的文章属于不同用户";
    public static final String FUNCTION_ARTICLE = "从方法参数获取批量文章用户ID: %d";
    public static final String MULTI_PATH = "获取路径多个参数失败: ";
    public static final String BODY_GET = "获取请求体参数失败: ";
    public static final String USERNAME_ID = "通过用户名 %s 获取用户ID: %d";
    public static final String OBJECT_PARAM = "从对象中提取用户ID失败: ";
    public static final String NO_SOURCE = "目标资源ID为空，无法检查所有权";
    public static final String PARAM_NAME = "获取参数名失败";

    // ===== 基础设施 =====
    public static final String CREATE_TABLE = "检查/创建表失败";
    public static final String NO_TABLE_CREATE = "表 '%s' 不存在，已创建";
    public static final String TABLE_EXIST = "表 '%s' 已存在";
    public static final String REDIS_USER = "Redis 使用用户名 '%s' 连接";
    public static final String REDIS_PASSWORD = "Redis 已设置密码认证";
    public static final String REDIS_CONNECT = "Redis 连接配置: {}:{} (DB: {})";
    public static final String LOG_INIT = "日志配置初始化完成，路径: {}";
    public static final String LOG_WRITE = "写入日志失败: {}";

    // ===== RabbitMQ =====
    public static final String RabbitMQ_SEND_SUCCESS = "API 日志已发送到队列: %s";
    public static final String RabbitMQ_SEND_FAIL = "向消息队列发送 API 日志出错: ";
    public static final String MQ_SEND = "发送到MQ：";
    public static final String MSG_SEND_SUCCESS = "消息发送成功：%s -> %s";
    public static final String MSG_SEND_FAIL = "消息发送失败：";
    public static final String EXCHANGE_SEND_SUCCESS = "发送消息到交换机成功：%s -> %s";
    public static final String EXCHANGE_SEND_FAIL = "发送消息到交换机失败: ";
    public static final String TRANSFORM_MSG_FAIL = "发送消息到交换机失败: ";

    // ===== 异常 =====
    public static final String BUSINESS_EXCEPTION = "捕获到业务异常: ";
    public static final String SYSTEM_EXCEPTION = "捕获到业系统异常: ";
    public static final String SYSTEM_EXCEPTION_BACK = "Spring服务器错误";
    public static final String USER_INTERCEPTOR = "请求体中非法的用户id: ";

    // ===== 定时任务 =====
    public static final String TASK_START = "开始执行定时清理过期 Token 任务";
    public static final String TASK_END = "定时清理过期 Token 任务执行完成";
    public static final String TASK_EXCEPTION = "定时清理过期 Token 任务执行异常: ";

    // ===== 内部令牌 =====
    public static final String INTERNAL_TOKEN_NOT_NULL = "内部服务令牌密钥不能为 null 或者为空";
    public static final String INTERNAL_TOKEN_INIT = "内部服务令牌密钥初始化完成";
    public static final String INTERNAL_TOKEN_MISSING = "缺少必需的内部服务令牌请求头";
    public static final String INTERNAL_TOKEN_VALIDATE_SUCCESS = "内部服务令牌验证成功";
    public static final String INTERNAL_TOKEN_EXPIRED = "内部服务令牌已过期";
    public static final String INTERNAL_TOKEN_INVALID = "内部服务令牌无效";
    public static final String INTERNAL_TOKEN_VALIDATION_FAIL = "内部服务令牌验证失败: ";
    public static final String SERVICE_NAME_MISMATCH = "服务名称不匹配";
    public static final String CANNOT_GET_HTTP_REQUEST = "无法获取当前HTTP请求";
    public static final String INTERNAL_TOKEN_VALIDATE_METHOD = "内部服务令牌验证成功，方法: ";

    // ===== 服务降级 =====
    public static final String FASTAPI_CALL_DEGRADED = "FastAPI 服务调用触发降级: ";
    public static final String FASTAPI_SERVICE_UNAVAILABLE = "FastAPI 服务暂时不可用，已触发降级";
    public static final String VECTOR_SYNC_SERVICE_UNAVAILABLE = "向量同步服务暂时不可用，已触发降级";
    public static final String ANALYSIS_CACHE_CLEANUP_SERVICE_UNAVAILABLE = "分析缓存清理服务暂时不可用，已触发降级";
    public static final String NEO4J_SYNC_SERVICE_UNAVAILABLE = "Neo4j同步服务暂时不可用，已触发降级";
    public static final String GOZERO_SERVICE_UNAVAILABLE = "GoZero 服务调用触发降级: ";
    public static final String GOZERO_SERVICE_UNAVAILABLE_DEGRADE = "GoZero 服务暂时不可用，已触发降级";
    public static final String ES_SERVICE_UNAVAILABLE = "ES 同步服务暂时不可用，已触发降级";
    public static final String NESTJS_SERVICE_UNAVAILABLE = "NestJS 服务调用触发降级: ";
    public static final String NESTJS_SERVICE_UNAVAILABLE_DEGRADE = "NestJS 服务暂时不可用，已触发降级";
    public static final String NESTJS_EMAIL_SERVICE_UNAVAILABLE = "NestJS 邮件服务调用触发降级: ";
    public static final String NESTJS_EMAIL_SERVICE_UNAVAILABLE_MSG = "邮件服务暂时不可用，请稍后再试";

    // ===== AI 初始化 =====
    public static final String INIT_AI = "初始化AI用户失败";
    public static final String AI_CREATED = "AI用户 '%s' (id: %d) 已创建";
    public static final String AI_EXIST = "AI用户 (id: %d) 已存在";
    public static final String AI_INSERT = "插入AI用户 (id: %d) 失败";

    // ===== Feign =====
    public static final String FEIGN_BUSINESS_ERROR_LOG = "Feign 调用返回业务错误: code=%d, msg=%s";
    public static final String FEIGN_CALL_FAIL = "业务调用失败: ";
    public static final String FEIGN_PARSE_WARNING = "Feign 响应解析异常，将使用默认解码器: ";
    public static final String FEIGN_DESERIALIZE_FAIL = "Feign 响应反序列化失败: ";
    public static final String FEIGN_UNKNOWN_ERROR = "未知错误";

    // ===== .env =====
    public static final String DOTENV_FILE_NOT_EXIST = "[DotenvLoader] .env文件不存在，跳过加载";
    public static final String DOTENV_LOAD_SUCCESS = "[DotenvLoader] 成功加载 {} 个环境变量";
    public static final String DOTENV_LOAD_FAIL = "[DotenvLoader] 加载.env文件失败: ";

    // ===== 分布式锁消息 =====
    public static final String LOCK_ACQUIRE_SUCCESS = "获取分布式锁成功，key: %s";
    public static final String LOCK_ACQUIRE_FAIL = "获取分布式锁失败，跳过本次执行，key: %s";
    public static final String LOCK_RELEASE_SUCCESS = "释放分布式锁成功，key: %s";
    public static final String LOCK_RELEASE_FAIL = "释放分布式锁失败，key: %s";
}
