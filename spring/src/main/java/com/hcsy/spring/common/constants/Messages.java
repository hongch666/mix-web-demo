package com.hcsy.spring.common.constants;

/**
 * 消息类常量 — 日志消息、用户提示、状态描述
 */
public class Messages {

    /**
     * 聚合日志消息、用户提示与错误描述等文案常量
     */
    private Messages() {
    }

    // ===== 错误信息 =====

    /** 收藏失败且可能重复收藏的用户提示 */
    public static final String COLLECT_FAIL = "收藏失败，可能已经收藏过了";
    /** 取消收藏时记录不存在的用户提示 */
    public static final String UNCOLLECT_FAIL = "取消收藏失败，记录不存在";
    /** 点赞失败且可能重复点赞的用户提示 */
    public static final String LIKE_FAIL = "点赞失败，可能已经点过赞了";
    /** 取消点赞时记录不存在的用户提示 */
    public static final String UNLIKE_FAIL = "取消点赞失败，记录不存在";
    /** 关注失败且可能重复关注的用户提示 */
    public static final String FOCUS_FAIL = "关注失败，可能已经关注过了";
    /** 取消关注时记录不存在的用户提示 */
    public static final String UNFOCUS_FAIL = "取消关注失败，记录不存在";

    // ===== 实体不存在 =====

    /** 用户不存在的提示 */
    public static final String UNDEFINED_USER = "用户不存在";
    /** 子分类不存在的提示 */
    public static final String UNDEFINED_SUB_CATEGORY = "子分类不存在";
    /** 文章不存在的提示 */
    public static final String UNDEFINED_ARTICLE = "文章不存在";
    /** 分类不存在的提示 */
    public static final String UNDEFINED_CATEGORY = "分类不存在";
    /** 文章不存在无法评论的提示 */
    public static final String UNDEFINED_ARTICLE_COMMENT = "文章不存在，无法评论";
    /** 部分或全部文章不存在的提示 */
    public static final String UNDEFINED_ARTICLES = "部分或全部文章不存在";
    /** 部分或全部用户不存在的提示 */
    public static final String UNDEFINED_USERS = "部分或全部用户不存在";
    /** 部分或全部分类不存在的提示 */
    public static final String UNDEFINED_CATEGORIES = "部分或全部分类不存在";
    /** 部分或全部子分类不存在的提示 */
    public static final String UNDEFINED_SUB_CATEGORIES = "部分或全部子分类不存在";
    /** 部分或全部评论不存在的提示 */
    public static final String UNDEFINED_COMMENTS = "部分或全部评论不存在";
    /** 分类缺失时使用的兜底名称 */
    public static final String UNCATEGORIZED = "未分类";
    /** 排序方式不受支持的提示前缀 */
    public static final String SORT_WAY = "不支持的排序方式: ";

    // ===== 登录/验证码 =====

    /** 用户名或密码错误的提示 */
    public static final String LOGIN = "用户名或密码错误";
    /** 邮箱验证码无效或已过期的提示 */
    public static final String VERIFY_CODE = "邮箱验证码无效或已过期";
    /** 图形验证码错误或已过期的提示 */
    public static final String IMAGE_CAPTCHA_INVALID = "图形验证码错误或已过期";
    /** 用户不存在需要先注册的提示 */
    public static final String UNDEFINED_USER_REGISTER = "用户不存在，请先注册";
    /** 邮箱已被注册的提示 */
    public static final String EMAIL_REGISTER = "邮箱已被注册";
    /** 邮箱未注册的提示 */
    public static final String EMAIL_UNREGISTER = "邮箱未注册，请先注册";
    /** 验证码类型不受支持的提示 */
    public static final String VERIFY_CODE_UNSUPPORT = "不支持的类型，请使用 register、login 或 reset";
    /** 邮箱格式不正确的提示 */
    public static final String EMAIL = "邮箱格式不正确";
    /** 没有可重置密码用户的提示 */
    public static final String PASSWORD_NO_USER = "没有用户可重置";
    /** 默认密码不能为空的提示 */
    public static final String USER_DEFAULT_PASSWORD_NOT_BLANK = "默认密码不能为空";
    /** 重置密码不能为空的提示 */
    public static final String USER_RESET_PASSWORD_NOT_BLANK = "重置密码不能为空";

    // ===== GitHub 登录 =====

    /** GitHub 注册账号禁止密码登录的提示 */
    public static final String GITHUB_ACCOUNT_PASSWORD_LOGIN_BLOCKED = "该账号通过 GitHub 登录创建，请使用 GitHub 登录或先设置密码";
    /** 缓存 GitHub 登录票据失败的日志消息 */
    public static final String GITHUB_LOGIN_TICKET_CACHE_FAILED = "缓存 GitHub 登录票据失败";
    /** GitHub 登录票据为空的提示 */
    public static final String GITHUB_TOKEN_TICKET_EMPTY = "GitHub 登录票据不能为空";
    /** GitHub 登录票据已过期的提示 */
    public static final String GITHUB_TOKEN_TICKET_EXPIRED = "GitHub 登录票据已过期，请重新登录";
    /** 解析 GitHub 登录票据失败的日志消息 */
    public static final String GITHUB_TOKEN_TICKET_PARSE_FAILED = "解析 GitHub 登录票据失败";

    // ===== 文章发布/阅读量 =====

    /** 文章不存在并附带 ID 的日志前缀 */
    public static final String UNDEFINED_ARTICLE_ID = "文章不存在，ID：";
    /** 文章作者不存在并附带 ID 的日志前缀 */
    public static final String UNDEFINED_ARTICLE_AUTHOR_ID = "文章作者不存在，ID：";
    /** 文章子分类不存在并附带 ID 的日志前缀 */
    public static final String UNDEFINED_SUB_CATEGORY_AUTHOR_ID = "文章子分类不存在，ID：";
    /** 子分类的父分类不存在并附带 ID 的日志前缀 */
    public static final String UNDEFINED_CATEGORY_AUTHOR_ID = "文章子分类的父分类不存在，ID：";
    /** 发布失败时文章不存在或更新失败的提示 */
    public static final String PUBLISH_ARTICLE = "发布失败：文章不存在或更新失败";
    /** 文章未发布无法增加阅读量的提示 */
    public static final String UNPUBLISH_ADD_VIEW = "文章未发布，无法增加阅读量";
    /** 增加阅读量失败时文章不存在或更新失败的提示 */
    public static final String ADD_VIEW_ARTICLE = "增加阅读量失败：文章不存在或更新失败";

    // ===== ES/Vector/数仓同步 =====

    /** 同步目标名称：ES */
    public static final String SYNC_TARGET_ES = "ES";
    /** 同步目标名称：向量库 */
    public static final String SYNC_TARGET_VECTOR = "向量库";
    /** 同步目标名称：数仓 */
    public static final String SYNC_TARGET_WAREHOUSE = "数仓";
    /** 触发同步的日志消息模板 */
    public static final String SYNC_TARGETS = "触发同步：%s...";
    /** ES 同步完成的日志消息 */
    public static final String SYNC_ES_SUCCESS = "ES 同步完成";
    /** 向量同步完成的日志消息 */
    public static final String SYNC_VECTOR_SUCCESS = "Vector 同步完成";
    /** 同步成功的日志消息模板 */
    public static final String SYNC_SUCCESS = "%s 同步完成，耗时: %dms";
    /** 同步失败的日志消息模板 */
    public static final String SYNC_FAIL = "%s 同步失败，耗时: %dms, 错误: %s";

    // ===== ClickHouse 数仓同步 =====

    /** 数仓同步已触发的日志消息 */
    public static final String WAREHOUSE_SYNC_SUCCESS = "ClickHouse 数仓同步已触发";
    /** 数仓同步资源不受支持的日志消息 */
    public static final String WAREHOUSE_UNSUPPORTED_RESOURCE = "不支持的数仓同步资源: %s";

    // ===== Neo4j 同步任务描述 =====

    /** Neo4j 同步任务开始执行的日志消息 */
    public static final String NEO4J_SYNC_TASK_START_MESSAGE = "Neo4j 同步任务开始执行，方法: %s，操作: %s";
    /** Neo4j 同步异步任务提交成功的日志消息 */
    public static final String NEO4J_SYNC_TASK_SUBMIT_SUCCESS_MESSAGE = "Neo4j 同步异步任务已提交，方法: %s，操作: %s";
    /** Neo4j 同步异步任务提交失败的日志消息 */
    public static final String NEO4J_SYNC_TASK_SUBMIT_FAIL_MESSAGE = "Neo4j 同步异步任务提交失败，方法: %s，操作: %s，错误: %s";
    /** Neo4j 同步调用失败的日志消息 */
    public static final String NEO4J_SYNC_CALL_FAIL_MESSAGE = "Neo4j 同步调用失败，方法: %s，操作: %s，返回信息: %s";
    /** Neo4j 同步调用返回空结果的日志消息 */
    public static final String NEO4J_SYNC_CALL_EMPTY_MESSAGE = "Neo4j 同步调用返回空结果，方法: %s，操作: %s";

    // ===== 缓存清理 =====

    /** 缓存写入失败的日志消息 */
    public static final String CACHE_WRITE_FAILED = "缓存写入失败，key=%s: %s";
    /** 缓存反序列化失败的日志消息 */
    public static final String CACHE_DESERIALIZE_FAILED = "缓存反序列化失败，key=%s: %s";
    /** 缓存读取失败的日志消息 */
    public static final String CACHE_READ_FAILED = "缓存读取失败，key=%s: %s";
    /** L2 缓存清除失败的日志消息 */
    public static final String CACHE_L2_CLEAR_FAILED = "L2缓存清除失败: %s";
    /** 发布本地缓存失效消息失败的日志消息 */
    public static final String CACHE_INVALIDATION_PUBLISH_FAILED = "发布本地缓存失效消息失败，频道=%s: %s";
    /** 订阅本地缓存失效消息失败的日志消息 */
    public static final String CACHE_INVALIDATION_SUBSCRIBE_FAILED = "订阅本地缓存失效消息失败，频道=%s: %s";
    /** 缓存名称不能为空的校验消息 */
    public static final String CACHE_OPTIONS_NAME_NOT_BLANK = "缓存名称不能为空";
    /** 缓存失效频道不能为空的校验消息 */
    public static final String CACHE_OPTIONS_CHANNEL_NOT_BLANK = "缓存失效频道不能为空";
    /** 缓存容量必须大于零的校验消息 */
    public static final String CACHE_OPTIONS_MAXIMUM_SIZE_POSITIVE = "缓存容量必须大于零";
    /** L1 缓存过期时间必须大于零的校验消息 */
    public static final String CACHE_OPTIONS_L1_TTL_POSITIVE = "L1 本地缓存过期时间必须大于零";
    /** L2 缓存过期时间必须大于零的校验消息 */
    public static final String CACHE_OPTIONS_L2_TTL_POSITIVE = "L2 缓存过期时间必须大于零";
    /** 子分类已存在权威参考文本的提示 */
    public static final String REFERENCE_EXIST = "该子分类已存在权威参考文本";
    /** 子分类暂无权威参考文本的提示 */
    public static final String REFERENCE_NOT_EXIST = "该子分类暂无权威参考文本";
    /** PDF 类型必须提供 pdf 链接的校验消息 */
    public static final String PDF_EMPTY = "PDF类型必须提供pdf链接";
    /** link 类型必须提供 link 链接的校验消息 */
    public static final String LINK_EMPTY = "link类型必须提供link链接";
    /** PDF 链接必须以 .pdf 结尾的校验消息 */
    public static final String PDF_TAIL = "PDF链接必须以.pdf结尾";

    // ===== 验证码 =====

    /** 验证码已写入 Redis 的日志前缀 */
    public static final String CODE_SAVE = "验证码已保存到 Redis: ";
    /** 验证码邮件发送成功的日志前缀 */
    public static final String CODE_SUCCESS = "验证码邮件已成功发送到: ";
    /** 验证码已过期或不存在的日志前缀 */
    public static final String CODE_EXPIRED = "验证码已过期或不存在: ";
    /** 验证码验证错误的日志前缀 */
    public static final String CODE_VERIFY_FAIL = "验证码验证错误: ";
    /** 邮箱验证成功的日志前缀 */
    public static final String CODE_VERIFY_SUCCESS = "邮箱验证成功: ";
    /** 验证码验证失败的日志前缀 */
    public static final String CODE_VERIFY_EXCEPTION = "验证码验证失败: ";
    /** 图形验证码已写入 Redis 的日志前缀 */
    public static final String IMAGE_CAPTCHA_SAVE = "图形验证码已保存到 Redis: ";
    /** 图形验证码已删除的日志前缀 */
    public static final String IMAGE_CAPTCHA_DELETE = "图形验证码已删除: ";
    /** 图形验证码已过期或不存在的日志前缀 */
    public static final String IMAGE_CAPTCHA_EXPIRED = "图形验证码已过期或不存在: ";
    /** 图形验证码校验失败的日志前缀 */
    public static final String IMAGE_CAPTCHA_VERIFY_FAIL = "图形验证码校验失败: ";
    /** 图形验证码校验成功的日志前缀 */
    public static final String IMAGE_CAPTCHA_VERIFY_SUCCESS = "图形验证码校验成功: ";

    // ===== JWT/Token =====

    /** 解析用户 ID 失败的日志消息 */
    public static final String EXPIRED_USER_FAIL = "解析用户 ID 失败: %s";
    /** JWT 密钥为空的校验消息 */
    public static final String JWT_NOT_NULL = "JWT 密钥不能为 null 或者为空";
    /** JWT 密钥初始化完成的日志消息 */
    public static final String JWT_INIT = "JWT 密钥初始化完成";
    /** Token 验证成功的日志消息 */
    public static final String TOKEN_VERIFY_SUCCESS = "Token验证成功";
    /** Token 已过期的提示 */
    public static final String TOKEN_EXPIRED = "Token已过期";
    /** 无效 Token 的提示 */
    public static final String UNUSED_TOKEN = "无效的Token";
    /** Token 类型错误的提示 */
    public static final String TOKEN_TYPE_INVALID = "Token类型错误，请使用正确的Token";
    /** 刷新令牌无效或已过期的提示 */
    public static final String REFRESH_TOKEN_INVALID = "Refresh Token 无效或已过期";
    /** Token 刷新成功的提示 */
    public static final String REFRESH_TOKEN_SUCCESS = "Token 刷新成功";
    /** 无法获取用户信息时要求登录的提示 */
    public static final String GET_USER_TOKEN_ID = "无法获取用户信息，请确保已登录";
    /** 用户未登录或登录已失效的提示 */
    public static final String USER_NOT_LOGIN = "用户未登录或登录已失效";
    /** 认证身份解析成功的日志消息 */
    public static final String AUTH_IDENTITY_RESOLVED = "认证身份解析成功 - 用户: {}, 会话: {}";
    /** 登录会话不存在的提示 */
    public static final String SESSION_NOT_FOUND = "登录会话不存在，请重新登录";
    /** 用户登录创建会话的日志消息 */
    public static final String LOGIN_SESSION_CREATED = "用户 %d 登录，创建会话 %s";
    /** 用户登出移除会话的日志消息 */
    public static final String LOGIN_SESSION_REMOVED = "用户 %d 登出，移除会话 %s";
    /** 用户登出后无其他会话且状态置为离线的日志消息 */
    public static final String REMOVE_SESSION_LOGOUT = "用户 %d 没有其他登录会话，状态已设为离线";
    /** 用户登出后仍有其他会话的日志消息 */
    public static final String REMOVE_SESSION = "用户 %d 登出，还有 %d 个登录会话";
    /** 管理员强制用户下线的日志消息 */
    public static final String ADMIN_SESSION_CLEAN = "管理员已将用户 %d 下线，共清除 %d 个登录会话";
    /** 清理会话的审计日志消息 */
    public static final String SESSION_CLEAN_LOG = "用户 %s 清理了 %d 个 Session";
    /** 定时任务清理过期会话完成的日志消息 */
    public static final String TOTAL_SESSION_CLEAN = "定时任务：清理完成，扫描 %d 个用户，共清除 %d 个过期 Session";

    // ===== AOP/权限 =====

    /** 接口日志的请求行格式 */
    public static final String API_LOG_START = "%s %s: %s";
    /** 接口日志的耗时格式 */
    public static final String API_LOG_DURATION = "%s %s 使用了%dms";
    /** 接口方法执行异常的错误消息 */
    public static final String API_EXCEPTION = "API方法执行异常";
    /** 参数解析失败的日志消息 */
    public static final String PARAM_EXPIRED = "参数解析失败";
    /** 格式化参数值失败的日志消息 */
    public static final String FORMAT_PARAM = "格式化参数值失败";
    /** 提取路径参数失败的日志消息 */
    public static final String PATH_PARAM = "提取路径参数失败";
    /** 提取请求体失败的日志消息 */
    public static final String BODY_PARAM = "提取请求体失败";
    /** 事务执行失败已回滚的日志消息 */
    public static final String TRANSACTION_ROLLBACK = "事务执行失败，已回滚";
    /** 未登录时使用默认用户 ID 的日志消息 */
    public static final String UNLOGIN_DEFAULT = "用户未登录，使用默认用户ID: -1";
    /** 用户名缺失时使用的占位名 */
    public static final String UNKNOWN_USERNAME = "unknown";
    /** HTTP 方法缺失时使用的占位值 */
    public static final String UNKNOWN_HTTP_METHOD = "UNKNOWN";
    /** 管理员权限校验直接通过的日志消息 */
    public static final String ADMIN_PASS = "用户具有管理员权限，直接通过";
    /** 权限不足无法执行操作的提示 */
    public static final String NO_PERMISSION = "权限不足，无法执行此操作";
    /** 获取目标资源 ID 失败的日志前缀 */
    public static final String TARGET_FAIL = "获取目标资源ID失败: ";
    /** 评论 ID 不存在的日志前缀 */
    public static final String COMMENT_ID = "评论ID不存在: ";
    /** 目标资源 ID 为空无法校验所有权的日志消息 */
    public static final String NO_SOURCE = "目标资源ID为空，无法检查所有权";
    /** 批量资源不属于同一用户的校验消息 */
    public static final String MULTIPLE_RESOURCE_OWNERS = "批量资源不属于同一用户";

    // ===== 基础设施 =====

    /** 检查或创建表失败的日志消息 */
    public static final String CREATE_TABLE = "检查/创建表失败";
    /** 日志配置初始化完成的日志消息 */
    public static final String LOG_INIT = "日志配置初始化完成，路径: {}";
    /** 写入日志失败的日志消息 */
    public static final String LOG_WRITE = "写入日志失败: {}";

    // ===== RabbitMQ =====

    /** 向消息队列发送 API 日志失败的日志前缀 */
    public static final String RabbitMQ_SEND_FAIL = "向消息队列发送 API 日志出错: ";
    /** 发送到消息队列的日志前缀 */
    public static final String MQ_SEND = "发送到MQ：";
    /** 消息发送成功的日志消息 */
    public static final String MSG_SEND_SUCCESS = "消息发送成功：%s -> %s";
    /** 消息发送失败的日志前缀 */
    public static final String MSG_SEND_FAIL = "消息发送失败：";
    /** 消息发送到交换机成功的日志消息 */
    public static final String EXCHANGE_SEND_SUCCESS = "发送消息到交换机成功：%s -> %s";
    /** 消息发送到交换机失败的日志前缀 */
    public static final String EXCHANGE_SEND_FAIL = "发送消息到交换机失败: ";
    /** 消息转换失败的日志消息 */
    public static final String TRANSFORM_MSG_FAIL = "消息转换失败";
    /** RabbitMQ 消息未确认的日志消息 */
    public static final String RABBITMQ_MESSAGE_UNCONFIRMED = "RabbitMQ 未确认消息";
    /** API 日志异步发送成功的日志消息 */
    public static final String ASYNC_API_LOG_SEND_SUCCESS = "API 日志异步发送成功";
    /** API 日志异步发送失败的日志消息 */
    public static final String ASYNC_API_LOG_SEND_FAILED = "API 日志异步发送失败: %s";

    // ===== 异常 =====

    /** 捕获到业务异常的日志前缀 */
    public static final String BUSINESS_EXCEPTION = "捕获到业务异常: ";
    /** 捕获到系统异常的日志前缀 */
    public static final String SYSTEM_EXCEPTION = "捕获到业系统异常: ";
    /** 未预期异常返回给调用方的兜底消息 */
    public static final String SYSTEM_EXCEPTION_BACK = "Spring服务器错误";
    /** 请求体格式不正确或参数类型不匹配的提示 */
    public static final String REQUEST_BODY_INVALID = "请求体格式不正确或参数类型不匹配";

    // ===== 定时任务 =====

    /** 过期 Token 清理任务开始的日志消息 */
    public static final String TASK_START = "开始执行定时清理过期 Token 任务";
    /** 过期 Token 清理任务完成的日志消息 */
    public static final String TASK_END = "定时清理过期 Token 任务执行完成";
    /** 过期 Token 清理任务异常的错误消息 */
    public static final String TASK_EXCEPTION = "定时清理过期 Token 任务执行异常: ";

    // ===== 内部SQL代理 =====

    /** 只允许只读查询的安全提示 */
    public static final String SQL_PROXY_FORBIDDEN_STATEMENT = "安全限制：只允许执行只读查询（SELECT/WITH/SHOW/DESC/DESCRIBE/EXPLAIN）";
    /** 表名不在白名单的安全提示 */
    public static final String SQL_PROXY_TABLE_NOT_IN_WHITELIST = "安全限制：表 '%s' 不在白名单内";
    /** 必须包含 LIMIT 子句的安全提示 */
    public static final String SQL_PROXY_LIMIT_REQUIRED = "安全限制：SQL查询必须包含LIMIT子句";
    /** LIMIT 超过上限的安全提示 */
    public static final String SQL_PROXY_LIMIT_EXCEEDED = "安全限制：LIMIT超过最大限制100";
    /** 禁止执行多条 SQL 的安全提示 */
    public static final String SQL_PROXY_MULTIPLE_STATEMENTS = "安全限制：禁止执行多条SQL语句";
    /** 获取表结构信息失败的日志消息 */
    public static final String SQL_PROXY_TABLE_SCHEMA_ERROR = "获取表结构信息失败: %s";
    /** 执行 SQL 查询失败的日志消息 */
    public static final String SQL_PROXY_QUERY_ERROR = "执行SQL查询失败: %s";

    // ===== 内部令牌 =====

    /** 内部服务令牌密钥为空的校验消息 */
    public static final String INTERNAL_TOKEN_NOT_NULL = "内部服务令牌密钥不能为 null 或者为空";
    /** 内部服务令牌密钥初始化完成的日志消息 */
    public static final String INTERNAL_TOKEN_INIT = "内部服务令牌密钥初始化完成";
    /** 请求头缺少内部服务令牌的错误消息 */
    public static final String INTERNAL_TOKEN_MISSING = "缺少必需的内部服务令牌请求头";
    /** 内部服务令牌校验成功的日志消息 */
    public static final String INTERNAL_TOKEN_VALIDATE_SUCCESS = "内部服务令牌验证成功";
    /** 内部服务令牌已过期的错误消息 */
    public static final String INTERNAL_TOKEN_EXPIRED = "内部服务令牌已过期";
    /** 内部服务令牌无效的错误消息 */
    public static final String INTERNAL_TOKEN_INVALID = "内部服务令牌无效";
    /** 内部服务令牌校验失败的日志前缀 */
    public static final String INTERNAL_TOKEN_VALIDATION_FAIL = "内部服务令牌验证失败: ";
    /** 内部服务令牌校验成功并附带方法的日志前缀 */
    public static final String INTERNAL_TOKEN_VALIDATE_METHOD = "内部服务令牌验证成功，方法: ";

    // ===== 服务降级 =====

    /** 向量同步服务不可用已降级的提示 */
    public static final String VECTOR_SYNC_SERVICE_UNAVAILABLE = "向量同步服务暂时不可用，已触发降级";
    /** 数仓同步服务不可用已降级的提示 */
    public static final String WAREHOUSE_SYNC_SERVICE_UNAVAILABLE = "数仓同步服务暂时不可用，已触发降级";
    /** Neo4j 同步服务不可用已降级的提示 */
    public static final String NEO4J_SYNC_SERVICE_UNAVAILABLE = "Neo4j同步服务暂时不可用，已触发降级";
    /** ES 同步服务不可用已降级的提示 */
    public static final String ES_SERVICE_UNAVAILABLE = "ES 同步服务暂时不可用，已触发降级";
    /** 邮件服务不可用的用户提示 */
    public static final String NESTJS_EMAIL_SERVICE_UNAVAILABLE_MSG = "邮件服务暂时不可用，请稍后再试";

    // ===== AI 初始化 =====

    /** AI 用户初始化完成的日志消息 */
    public static final String INIT_AI_SUCCESS = "AI用户初始化完成";
    /** AI 用户创建成功的日志消息 */
    public static final String AI_CREATED = "AI用户 '%s' (id: %d) 已创建";
    /** AI 用户已存在的日志消息 */
    public static final String AI_EXIST = "AI用户 (id: %d) 已存在";
    /** 插入 AI 用户失败的日志消息 */
    public static final String AI_INSERT = "插入AI用户 (id: %d) 失败";

    // ===== .env =====

    /** .env 文件不存在跳过加载的日志消息 */
    public static final String DOTENV_FILE_NOT_EXIST = "[DotenvLoader] .env文件不存在，跳过加载";
    /** .env 文件加载成功的日志消息 */
    public static final String DOTENV_LOAD_SUCCESS = "[DotenvLoader] 成功加载 {} 个环境变量";
    /** .env 文件加载失败的日志消息 */
    public static final String DOTENV_LOAD_FAIL = "[DotenvLoader] 加载.env文件失败: ";

    // ===== 分布式锁消息 =====

    /** 分布式锁获取成功的日志消息 */
    public static final String LOCK_ACQUIRE_SUCCESS = "获取分布式锁成功，key: %s";
    /** 分布式锁获取失败跳过执行的日志消息 */
    public static final String LOCK_ACQUIRE_FAIL = "获取分布式锁失败，跳过本次执行，key: %s";
    /** 分布式锁释放成功的日志消息 */
    public static final String LOCK_RELEASE_SUCCESS = "释放分布式锁成功，key: %s";
    /** 分布式锁释放失败的日志消息 */
    public static final String LOCK_RELEASE_FAIL = "释放分布式锁失败，key: %s";
}
