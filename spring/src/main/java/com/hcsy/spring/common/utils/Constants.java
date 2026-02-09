package com.hcsy.spring.common.utils;

public class Constants {
    // 错误信息

    /**
     * 收藏失败信息
     */
    public static String COLLECT_FAIL = "收藏失败，可能已经收藏过了";

    /**
     * 取消收藏失败信息
     */
    public static String UNCOLLECT_FAIL = "取消收藏失败，记录不存在";

    /**
     * 点赞失败消息
     */
    public static String LIKE_FAIL = "点赞失败，可能已经点过赞了";

    /**
     * 取消点赞失败消息
     */
    public static String UNLIKE_FAIL = "取消点赞失败，记录不存在";

    /**
     * 关注失败消息
     */
    public static String FOCUS_FAIL = "关注失败，可能已经关注过了";

    /**
     * 取消关注失败消息
     */
    public static String UNFOCUS_FAIL = "取消关注失败，记录不存在";

    /**
     * 用户不存在信息
     */
    public static String UNDEFINED_USER = "用户不存在";

    /**
     * 子分类ID为空的消息
     */
    public static String UNDEFINED_SUB_CATEGORY_ID = "子分类ID不能为空";

    /**
     * 子分类不存在消息
     */
    public static String UNDEFINED_SUB_CATEGORY = "子分类不存在";

    /**
     * 文章不存在消息
     */
    public static String UNDEFINED_ARTICLE = "文章不存在";

    /**
     * 分类不存在消息
     */
    public static String UNDEFINED_CATEGORY = "分类不存在";

    /**
     * 文章不存在的评论错误信息
     */
    public static String UNDEFINED_ARTICLE_COMMENT = "文章不存在，无法评论";

    /**
     * 用户不存在的评论错误信息
     */
    public static String UNDEFINED_USER_COMMENT = "用户不存在，无法评论";

    /**
     * 批量文章不存在错误信息
     */
    public static String UNDEFINED_ARTICLES = "部分或全部文章不存在";

    /**
     * 批量用户不存在错误信息
     */
    public static String UNDEFINED_USERS = "部分或全部用户不存在";

    /**
     * 批量分类不存在错误信息
     */
    public static String UNDEFINED_CATEGORIES = "部分或全部分类不存在";

    /**
     * 批量子分类不存在错误信息
     */
    public static String UNDEFINED_SUB_CATEGORIES = "部分或全部子分类不存在";

    /**
     * 批量评论不存在错误信息
     */
    public static String UNDEFINED_COMMENTS = "部分或全部评论不存在";

    /**
     * 排序方式错误提示
     * 要在后面加上错误的排序类型
     */
    public static String SORT_WAY = "不支持的排序方式: ";

    /**
     * 登录错误
     */
    public static String LOGIN = "用户名或密码错误";

    /**
     * 验证码错误
     */
    public static String VERIFY_CODE = "邮箱验证码无效或已过期";

    /**
     * 用户不存在的注册消息
     */
    public static String UNDEFINED_USER_REGISTER = "用户不存在，请先注册";

    /**
     * 邮箱登录错误
     */
    public static String EMAIL_LOGIN = "邮箱验证码登录失败";

    /**
     * 登出错误
     */
    public static String LOGOUT = "登出失败";

    /**
     * 手动下线用户错误
     */
    public static String FORCE_LOGOUT = "手动下线用户失败";

    /**
     * 邮箱注册过的错误
     */
    public static String EMAIL_REGISTER = "邮箱已被注册";

    /**
     * 邮箱未注册错误
     */
    public static String EMAIL_UNREGISTER = "邮箱未注册，请先注册";

    /**
     * 验证码不支持错误
     */
    public static String VERIFY_CODE_UNSUPPORT = "不支持的类型，请使用 register、login 或 reset";

    /**
     * 发送验证码错误
     */
    public static String SEND_VERIFY_CODE = "发送验证码异常";

    /**
     * 邮箱格式错误
     */
    public static String EMAIL = "邮箱格式不正确";

    /**
     * 密码重置错误
     */
    public static String PASSWORD_RESET = "重置密码失败";

    /**
     * 所有密码重置错误
     */
    public static String PASSWORD_RESET_ALL = "重置所有用户密码失败";

    /**
     * 重置密码无用户
     */
    public static String PASSWORD_NO_USER = "没有用户可重置";

    /**
     * 用户密码重置错误
     */
    public static String PASSWORD_RESET_USER = "重置用户密码失败";

    /**
     * 文章不存在的id返回
     */
    public static String UNDEFINED_ARTICLE_ID = "文章不存在，ID：";

    /**
     * 文章作者id不存在的id返回
     */
    public static String UNDEFINED_ARTICLE_ID_AUTHOR_ID = "文章作者ID为空，文章ID：";

    /**
     * 文章作者不存在的id返回
     */
    public static String UNDEFINED_ARTICLE_AUTHOR_ID = "文章作者不存在，ID：";

    /**
     * 文章子分类id不存在的id返回
     */
    public static String UNDEFINED_SUB_CATEGORY_ID_AUTHOR_ID = "文章子分类ID为空，文章ID：";

    /**
     * 文章子分类不存在的id返回
     */
    public static String UNDEFINED_SUB_CATEGORY_AUTHOR_ID = "文章子分类不存在，ID：";

    /**
     * 文章分类id不存在的id返回
     */
    public static String UNDEFINED_CATEGORY_ID_AUTHOR_ID = "文章子分类的父分类ID为空，子分类ID：";

    /**
     * 文章分类不存在的id返回
     */
    public static String UNDEFINED_CATEGORY_AUTHOR_ID = "文章子分类的父分类不存在，ID：";

    /**
     * 文章发布失败错误信息
     */
    public static String PUBLISH_ARTICLE = "发布失败：文章不存在或更新失败";

    /**
     * 文章未发布导致的增加阅读量错误
     */
    public static String UNPUBLISH_ADD_VIEW = "文章未发布，无法增加阅读量";

    /**
     * 文章增加阅读量失败错误信息
     */
    public static String ADD_VIEW_ARTICLE = "增加阅读量失败：文章不存在或更新失败";

    /**
     * 触发同步信息
     */
    public static String SYNC = "触发同步 ES、Hive 和 Vector...";

    /**
     * 触发同步Hive信息
     */
    public static String SYNC_HIVE = "触发 Hive 同步";

    /**
     * ES同步成功
     */
    public static String SYNC_ES_SUCCESS = "ES 同步完成";

    /**
     * ES同步失败
     */
    public static String SYNC_ES_FAIL = "ES 同步失败: ";

    /**
     * Hive同步成功
     */
    public static String SYNC_HIVE_SUCCESS = "Hive 同步完成";

    /**
     * Hive同步失败
     */
    public static String SYNC_HIVE_FAIL = "Hive 同步失败: ";

    /**
     * Vector同步成功
     */
    public static String SYNC_VECTOR_SUCCESS = "Vector 同步完成";

    /**
     * Vector同步失败
     */
    public static String SYNC_VECTOR_FAIL = "Vector 同步失败: ";

    /**
     * 所有同步成功
     */
    public static String SYNC_ALL_SUCCESS = "所有同步任务执行完毕";

    /**
     * 所有同步失败
     */
    public static String SYNC_ALL_FAIL = "同步过程发生未知异常: ";

    /**
     * 清理Context消息
     */
    public static String CLEAN_CONTEXT = "UserContext 已清理";

    /**
     * 分类缓存加载信息
     */

    public static String CATEGORY_CACHE = "缓存未命中，从数据库加载 category";

    /**
     * 分类缓存分页加载信息
     */

    public static String CATEGORY_CACHE_PAGE = "缓存未命中，从数据库加载分页数据";

    /**
     * 权威文本已存在消息
     */
    public static String REFERENCE_EXIST = "该子分类已存在权威参考文本";

    /**
     * PDF为空提示
     */
    public static String PDF_EMPTY = "PDF类型必须提供pdf链接";

    /**
     * link为空提示
     */
    public static String LINK_EMPTY = "link类型必须提供link链接";

    /**
     * PDF结尾后缀提示
     */
    public static String PDF_TAIL = "PDF链接必须以.pdf结尾";

    /**
     * 验证码保存消息
     */
    public static String CODE_SAVE = "验证码已保存到 Redis: ";

    /**
     * 邮箱验证码信息
     */
    public static String EMAIL_CODE = "邮箱验证码";

    /**
     * 验证码发送成功
     */
    public static String CODE_SUCCESS = "验证码邮件已成功发送到: ";

    /**
     * 验证码发送失败
     */
    public static String CODE_FAIL = "邮件发送失败 (MessagingException): ";

    /**
     * 验证码发送异常
     */
    public static String CODE_EXCEPTION = "邮件发送异常: ";

    /**
     * 删除验证码消息
     */
    public static String CODE_DELETE = "已删除过期的验证码: ";

    /**
     * 验证码过期
     */
    public static String CODE_EXPIRED = "验证码已过期或不存在: ";

    /**
     * 验证码验证错误
     */
    public static String CODE_VERIFY_FAIL = "验证码验证错误: ";

    /**
     * 验证码验证成功
     */
    public static String CODE_VERIFY_SUCCESS = "邮箱验证成功: ";

    /**
     * 验证码验证异常
     */
    public static String CODE_VERIFY_EXCEPTION = "验证码验证失败: ";

    /**
     * 用户登录token保存消息
     */
    public static String LOGIN_TOKEN = "用户 %d 登录，Token 已保存到 Redis";

    /**
     * 移除Token离线信息
     */
    public static String REMOVE_TOKEN_LOGOUT = "用户 %d 没有其他登录会话，状态已设为离线";

    /**
     * 移除Token消息
     */
    public static String REMOVE_TOKEN = "用户 %d 登出，还有 %d 个登录会话";

    /**
     * 检查Token在Redis列表的消息
     */
    public static String TOKEN_REDIS = "用户 %d 的 Token 不在 Redis 列表中，可能已被管理员踢下线";

    /**
     * Token过期移除消息
     */
    public static String TOKEN_EXPIRED_CLEAN = "用户 %d 的 Token 已过期或格式错误，将从 Redis 列表中移除";

    /**
     * 验证Token错误信息
     */
    public static String VERIFY_TOKEN = "验证用户 %d 的 Token 时出错";

    /**
     * 管理员下线Token消息
     */
    public static String ADMIN_TOKEN_CLEAN = "管理员已将用户 %d 下线，共清除 %d 个登录会话";

    /**
     * 定时任务没有要清理的Token
     */
    public static String TASK_NO_CLEAN = "定时任务：没有需要清理的 Token";

    /**
     * 移除过期Token
     */
    public static String REMOVE_EXPIRED_TOKEN = "移除过期 Token: %s";

    /**
     * 移除无效Token
     */
    public static String REMOVE_INVALID_TOKEN = "移除过期 Token: %s";

    /**
     * 无有效Token标记离线消息
     */
    public static String NO_TOKEN_LOGOUT = "用户 %d 没有有效 Token，已标记为离线";

    /**
     * 解析用户失败消息
     */
    public static String EXPIRED_USER_FAIL = "解析用户 ID 失败: %s";

    /**
     * 清理用户的Token数消息
     */
    public static String USER_TOKEN_CLEAN = "用户 %s 清理了 %d 个 Token";

    /**
     * 总共清理Token统计消息
     */
    public static String TOTAL_CLEAN = "定时任务：清理完成，扫描 %d 个用户，共清除 %d 个过期 Token";

    /**
     * API异常消息
     */
    public static String API_EXCEPTION = "API方法执行异常";

    /**
     * 记录时间失败消息
     */
    public static String TIME_FAIL = "记录执行时间失败";

    /**
     * 参数解析失败消息
     */
    public static String PARAM_EXPIRED = "参数解析失败";

    /**
     * 格式化参数失败消息
     */
    public static String FORMAT_PARAM = "格式化参数值失败";

    /**
     * 对象转Map失败消息
     */
    public static String OBJECT_TO_MAP = "对象转Map失败";

    /**
     * 消息队列发送成功消息
     */
    public static String RabbitMQ_SEND_SUCCESS = "API 日志已发送到队列: %s";

    /**
     * 消息队列发送失败消息
     */
    public static String RabbitMQ_SEND_FAIL = "向消息队列发送 API 日志出错: ";

    /**
     * 路径参数失败消息
     */
    public static String PATH_PARAM = "提取路径参数失败";

    /**
     * 请求头参数失败消息
     */
    public static String BODY_PARAM = "提取请求体失败";

    /**
     * 发送MQ消息
     */
    public static String MQ_SEND = "发送到MQ：";

    /**
     * 触发同步消息
     */
    public static String TRIGGER_SYNC = "事务提交后触发异步同步任务";

    /**
     * 不同步类型提示消息
     */
    public static String UNSYNC_TYPE = "点赞/收藏/关注类操作不同步";

    /**
     * 事务失败回滚消息
     */
    public static String TRANSACTION_ROLLBACK = "事务执行失败，已回滚";

    /**
     * 未知操作消息
     */
    public static String UNKNOWN_OPERATION = "AOP识别失败：未知的操作类型";

    /**
     * 用户未登录的默认消息
     */
    public static String UNLOGIN_DEFAULT = "用户未登录，使用默认用户ID: -1";

    /**
     * 管理员直接通过消息
     */
    public static String ADMIN_PASS = "用户具有管理员权限，直接通过";

    /**
     * 目标资源信息
     */
    public static String TARGET_SOURCE = "当前用户ID: %d, 业务类型: %s, 参数来源: %s, 目标资源ID: %s";

    /**
     * 权限不足提示消息
     */
    public static String NO_PERMISION = "权限不足，无法执行此操作";

    /**
     * 权限检查失败消息
     */
    public static String PERMITION_FAIL = "权限检查失败";

    /**
     * 获取目标资源失败消息
     */
    public static String TARGET_FAIL = "获取目标资源ID失败: ";

    /**
     * 方法参数获取路径参数消息
     */
    public static String FUNCTION_PATH = "从方法参数获取路径参数 %s = %d";

    /**
     * 路径参数提取失败
     */
    public static String FUNCTION_PATH_FAIL = "路径参数转换失败: ";

    /**
     * URL获取ID
     */
    public static String URL_ID = "从URL路径获取ID: %d";

    /**
     * URL获取ID失败
     */
    public static String URL_ID_FAIL = "URL最后一个路径段不是数字: %s";

    /**
     * 获取单个路径参数失败消息
     */
    public static String SINGLE_PATH = "获取路径单个参数失败: ";

    /**
     * 评论id不存在消息
     */
    public static String COMMENT_ID = "评论ID不存在: ";

    /**
     * 评论无关联用户消息
     */
    public static String COMMENT_NO_USER = "评论ID未关联用户: ";

    /**
     * 评论属于不同用户消息
     */
    public static String COMMENT_MULTI_USER = "批量删除的评论属于不同用户";

    /**
     * 方法参数获取评论id消息
     */
    public static String FUNCTION_COMMENT = "从方法参数获取批量评论用户ID: %d";

    /**
     * 文章id不存在消息
     */
    public static String ARTICLE_ID = "文章ID不存在: ";

    /**
     * 文章无关联用户消息
     */
    public static String ARTICLE_NO_USER = "文章ID未关联用户: ";

    /**
     * 文章属于不同用户消息
     */
    public static String ARTICLE_MULTI_USER = "批量删除的文章属于不同用户";

    /**
     * 方法参数获取文章id消息
     */
    public static String FUNCTION_ARTICLE = "从方法参数获取批量文章用户ID: %d";

    /**
     * 获取多个路径参数失败消息
     */
    public static String MULTI_PATH = "获取路径多个参数失败: ";

    /**
     * 获取请求头失败消息
     */
    public static String BODY_GET = "获取请求体参数失败: ";

    /**
     * 通过用户名获取用户id消息
     */
    public static String USERNAME_ID = "通过用户名 %s 获取用户ID: %d";

    /**
     * 对象提取用户参数失败消息
     */
    public static String OBJECT_PARAM = "从对象中提取用户ID失败: ";

    /**
     * 目标资源为空消息
     */
    public static String NO_SOURCE = "目标资源ID为空，无法检查所有权";

    /**
     * 获取参数名失败消息
     */
    public static String PARAM_NAME = "获取参数名失败";

    /**
     * 创建表失败消息
     */
    public static String CREATE_TABLE = "检查/创建表失败";

    /**
     * 表不存在创建消息
     */
    public static String NO_TABLE_CREATE = "表 '%s' 不存在，已创建";

    /**
     * 表不已存在消息
     */
    public static String TABLE_EXIST = "表 '%s' 已存在";

    /**
     * 初始化AI用户失败消息
     */
    public static String INIT_AI = "初始化AI用户失败";

    /**
     * AI用户已创建消息
     */
    public static String AI_CREATED = "AI用户 '%s' (id: %d) 已创建";

    /**
     * AI用户已存在消息
     */
    public static String AI_EXIST = "AI用户 (id: %d) 已存在";

    /**
     * 插入AI用户消息
     */
    public static String AI_INSERT = "插入AI用户 (id: %d) 失败";

    /**
     * Redis用户连接消息
     */
    public static String REDIS_USER = "Redis 使用用户名 '%s' 连接";

    /**
     * Redis密码连接消息
     */
    public static String REDIS_PASSWORD = "Redis 已设置密码认证";

    /**
     * Redis连接消息
     */
    public static String REDIS_CONNECT = "Redis 连接配置: {}:{} (DB: {})";

    /**
     * 业务异常消息
     */
    public static String BUSINESS_EXCEPTION = "捕获到业务异常: ";

    /**
     * 系统异常消息
     */
    public static String SYSTEM_EXCEPTION = "捕获到业系统异常: ";

    /**
     * 系统异常返回消息
     */
    public static String SYSTEM_EXCEPTION_BACK = "Spring服务器错误";

    /**
     * 用户拦截ID异常消息
     */
    public static String USER_INTERCEPTOR = "请求体中非法的用户id: ";

    /**
     * 定时任务开始消息
     */
    public static String TASK_START = "开始执行定时清理过期 Token 任务";

    /**
     * 定时任务结束消息
     */
    public static String TASK_END = "定时清理过期 Token 任务执行完成";

    /**
     * 定时任务异常消息
     */
    public static String TASK_EXCEPTION = "定时清理过期 Token 任务执行异常: ";

    /**
     * JWT密钥不能为空异常消息
     */
    public static String JWT_NOT_NULL = "JWT 密钥不能为 null 或者为空";

    /**
     * JWT密钥初始化完成消息
     */
    public static String JWT_INIT = "JWT 密钥初始化完成";

    /**
     * Token验证成功消息
     */
    public static String TOKEN_VERIFY_SUCCESS = "Token验证成功";

    /**
     * Token过期消息
     */
    public static String TOKEN_EXPIRED = "Token已过期";

    /**
     * 无效Token消息
     */
    public static String UNUSED_TOKEN = "无效的Token";

    /**
     * 日志配置初始化消息
     */
    public static String LOG_INIT = "日志配置初始化完成，路径: {}";

    /**
     * 写入日志失败消息
     */
    public static String LOG_WRITE = "写入日志失败: {}";

    /**
     * 消息发送成功消息
     */
    public static String MSG_SEND_SUCCESS = "消息发送成功：%s -> %s";

    /**
     * 消息发送失败消息
     */
    public static String MSG_SEND_FAIL = "消息发送失败：";

    /**
     * 交换机发送成功消息
     */
    public static String EXCHANGE_SEND_SUCCESS = "发送消息到交换机成功：%s -> %s";

    /**
     * 交换机发送失败消息
     */
    public static String EXCHANGE_SEND_FAIL = "发送消息到交换机失败: ";

    /**
     * 消息转换失败消息
     */
    public static String TRANSFORM_MSG_FAIL = "发送消息到交换机失败: ";

    /**
     * 无法获取用户Token和id消息
     */
    public static String GET_USER_TOKEN_ID = "无法获取用户信息，请确保已登录";

    /**
     * 踢出其他设备失败消息
     */
    public static String KICK_FAIL = "踢出其他设备失败";

    /**
     * 令牌生成失败消息
     */
    public static String TOKEN_GEN_FAIL = "令牌生成失败";

    // 默认返回值

    /**
     * 文章默认返回
     */
    public static String DEFAULT_ARTICLE = "未知文章";

    /**
     * 用户默认返回
     */
    public static String DEFAULT_USER = "未知用户";

    /**
     * 用户id默认返回
     */
    public static String DEFAULT_USER_ID = "0";

    /**
     * AI 默认返回
     */
    public static String DEFAULT_AI = "未知AI";

    /**
     * 测试接口消息
     */
    public static String TEST = "Hello,I am Spring!";

    /**
     * 重置默认密码
     */
    public static String DEFAULT_PASSWORD = "123456";

    // AI用户相关常量

    /**
     * 豆包用户id
     */
    public static long DOUBAO_ID = 1001L;

    /**
     * 豆包用户名
     */
    public static String DOUBAO_NAME = "豆包";

    /**
     * 豆包邮箱
     */
    public static String DOUBAO_EMAIL = "doubao@example.com";

    /**
     * 豆包头像链接
     */
    public static String DOUBAO_IMG = "https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/%E8%B1%86%E5%8C%85.jpeg";

    /**
     * Gemini用户id
     */
    public static long GEMINI_ID = 1002L;

    /**
     * Gemini用户名
     */
    public static String GEMINI_NAME = "Gemini";

    /**
     * Gemini邮箱
     */
    public static String GEMINI_EMAIL = "gemini@example.com";

    /**
     * Gemini头像链接
     */
    public static String GEMINI_IMG = "https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/gemini.jpeg";

    /**
     * Qwen用户id
     */
    public static long QWEN_ID = 1003L;

    /**
     * Qwen用户名
     */
    public static String QWEN_NAME = "Qwen";

    /**
     * Qwen邮箱
     */
    public static String QWEN_EMAIL = "qwen@example.com";

    /**
     * Qwen头像链接
     */
    public static String QWEN_IMG = "https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/%E9%80%9A%E4%B9%89%E5%8D%83%E9%97%AE.jpeg";

    /**
     * 通用隐藏密码
     */
    public static String HIDE_PASSWORD = "******";

    // Swagger 消息常量

    /**
     * Swagger 标题
     */
    public static String SWAGGER_TITLE = "Spring部分的Swagger文档";

    /**
     * Swagger 版本
     */
    public static String SWAGGER_VERSION = "1.0.0";

    /**
     * Swagger 描述
     */
    public static String SWAGGER_DESC = "这是项目的Spring部分的Swagger文档";

    /**
     * Swagger URL 前缀
     */
    public static String SWAGGER_URL_PREFIX = "http://localhost:";

    // 初始消息常量

    /**
     * 初始输出IP
     */
    public static String INIT_IP = "localhost";

    /**
     * 初始输出端口
     */
    public static String INIT_PORT = "8081";

    /**
     * 初始输出信息
     */
    public static String INIT_MSG = "Spring Boot应用已启动";

    /**
     * 服务地址输出信息
     */
    public static String INIT_ADDR = "服务地址: http://{}:{}/";

    /**
     * 服务地址输出信息
     */
    public static String INIT_SWAGGER_ADDR = "Swagger文档地址: http://{}:{}/swagger-ui/index.html";

    // 内部服务令牌相关常量

    /**
     * 内部令牌密钥不能为空异常消息
     */
    public static String INTERNAL_TOKEN_NOT_NULL = "内部服务令牌密钥不能为 null 或者为空";

    /**
     * 内部令牌密钥初始化完成消息
     */
    public static String INTERNAL_TOKEN_INIT = "内部服务令牌密钥初始化完成";

    /**
     * 缺少内部令牌请求头错误消息
     */
    public static String INTERNAL_TOKEN_MISSING = "缺少必需的内部服务令牌请求头";

    /**
     * 内部令牌验证成功消息
     */
    public static String INTERNAL_TOKEN_VALIDATE_SUCCESS = "内部服务令牌验证成功";

    /**
     * 内部令牌已过期错误消息
     */
    public static String INTERNAL_TOKEN_EXPIRED = "内部服务令牌已过期";

    /**
     * 内部令牌无效错误消息
     */
    public static String INTERNAL_TOKEN_INVALID = "内部服务令牌无效";

    /**
     * 内部令牌验证失败错误消息
     */
    public static String INTERNAL_TOKEN_VALIDATION_FAIL = "内部服务令牌验证失败: ";

    /**
     * 服务名称不匹配错误消息
     */
    public static String SERVICE_NAME_MISMATCH = "服务名称不匹配";

    /**
     * 无法获取HTTP请求错误消息
     */
    public static String CANNOT_GET_HTTP_REQUEST = "无法获取当前HTTP请求";

    /**
     * 内部令牌验证方法调试消息
     */
    public static String INTERNAL_TOKEN_VALIDATE_METHOD = "内部服务令牌验证成功，方法: ";
}
