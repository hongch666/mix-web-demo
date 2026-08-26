package constants

// 消息类常量 — 日志消息、用户提示、状态描述
const (
	// 测试/启动
	TEST_MESSAGE         = "Hello,I am GoZero!"
	SERVER_START_MESSAGE = "服务启动于 %s:%d..."
	SWAGGER_DOCS_MESSAGE = "Swagger 文档地址 http://%s:%d/swagger/index.html"
	INIT_IP              = "127.0.0.1"
	SERVER_START_SUCCESS = "服务启动成功"
	GET_SWAGGER_FAIL     = "获取 Swagger 文档失败"

	// Nacos
	REGISTER_NACOS_DEV_MODE_MESSAGE = "SERVER_MODE=dev，Nacos 注册统一使用 127.0.0.1"
	NACOS_CACHE_DIR_CREATE_FAIL     = "创建Nacos缓存目录失败: %v, 路径: %s"
	NACOS_LOG_DIR_CREATE_FAIL       = "创建Nacos日志目录失败: %v, 路径: %s"
	GODOTENV_LOAD_FAIL              = "加载.env文件失败: %v"

	// 错误
	INTERNAL_TOKEN_SECRET_NOT_NULL = "内部服务令牌密钥不能为空"
	INTERNAL_TOKEN_INIT_FAIL       = "内部服务令牌初始化失败: %v"
	INTERNAL_TOKEN_NOT_INITIALIZED = "内部服务令牌未初始化"
	INTERNAL_TOKEN_MISSING         = "缺少必需的内部服务令牌请求头"
	INTERNAL_TOKEN_INVALID         = "内部服务令牌无效"
	INTERNAL_TOKEN_EXPIRED         = "内部服务令牌已过期"
	SERVICE_NAME_MISMATCH          = "服务名称不匹配"

	// 搜索
	SEARCH_ERR             = "文章搜索错误"
	SEARCH_MSG             = "发起了文章搜索"
	SEARCH_EXECUTION_ERROR = "搜索执行错误"
	ARTICLE_SEARCH_SUCCESS = "文章搜索成功"

	// WebSocket
	WS_SEND_SUCCESS                          = "消息 %d 通过WebSocket发送成功，已标记为已读"
	WS_SEND_FAIL                             = "用户 %d 不在线，消息 %d 已保存为未读"
	WS_SERIALIZE_MESSAGE_ERROR               = "序列化WebSocket消息失败: %v"
	WS_CLOSE_FRAME_SEND_FAIL                 = "发送WebSocket关闭帧失败: %v"
	WS_HEARTBEAT_RESPONSE_FAIL               = "序列化WebSocket心跳响应失败: %v"
	MESSAGE_SEND_ERROR                       = "消息发送失败"
	MARK_READ_FAIL                           = "标记消息 %d 为已读失败"
	WS_ERROR                                 = "WebSocket 错误: %v"
	PARSE_MESSAGE_FAIL                       = "解析消息失败: %v"
	WEBSOCKET_CONNECTION_ESTABLISHED_MESSAGE = "WebSocket 连接已建立"
	WS_CONNECT_FAIL                          = "WebSocket连接失败"
	WS_WRITE_MESSAGE_FAIL                    = "WebSocket 写消息失败: %v"
	USER_CONNECTED                           = "joined"
	USER_ALREADY_IN_QUEUE                    = "already_in_queue"
	USER_DISCONNECTED                        = "left"
	USER_NOT_IN_QUEUE                        = "not_in_queue"
	HEARTBEAT_MESSAGE                        = "ping"
	HEARTBEAT_RESPONSE                       = "pong"

	// SSE
	SSE_SERIALIZE_MESSAGE_EMPTY        = "序列化后的SSE消息为null"
	SSE_CONNECTION_ESTABLISHED_MESSAGE = "SSE 连接已建立"
	SSE_HEARTBEAT_WRITE_FAIL           = "SSE心跳写入失败: "
	EMPTY_SSE                          = "跳过空的SSE消息"
	SSE_WRITE_FAIL                     = "SSE写入失败: "
	SSE_HEARTBEAT                      = ": heartbeat\n\n"
	SSE_INIT_MESSAGE_SEND_FAIL         = "SSE初始化消息写入失败: %v"

	// 聊天
	CREATE_MESSAGE_ERROR                   = "消息创建错误"
	GET_HISTORY_MESSAGE_ERROR              = "获取消息历史错误"
	GET_UNREAD_COUNT_ERROR                 = "获取两个用户间未读消息数错误"
	GET_ALL_UNREAD_COUNTS_ERROR            = "获取用户与其他所有人的未读消息数错误"
	GET_UNREAD_COUNT_MESSAGE_ERROR         = "获取未读消息数失败: %v"
	CHAT_MESSAGE_SEND_SUCCESS              = "聊天消息发送成功"
	GET_CHAT_HISTORY_SUCCESS               = "获取聊天历史成功"
	GET_UNREAD_COUNT_SUCCESS               = "获取未读消息数成功"
	GET_ALL_UNREAD_COUNTS_SUCCESS          = "获取所有未读消息数成功"
	JOIN_QUEUE_SUCCESS                     = "加入聊天队列成功"
	LEAVE_QUEUE_SUCCESS                    = "离开聊天队列成功"
	GET_QUEUE_STATUS_SUCCESS               = "获取队列状态成功"
	USER_JOINED_QUEUE_MESSAGE              = "用户已加入聊天队列"
	USER_LEFT_QUEUE_MESSAGE                = "用户已离开聊天队列"
	USER_IN_QUEUE_NOT_CONNECTED_WARNING    = "用户在队列中但没有WebSocket连接，无法发送实时消息"
	SSE_REGISTER_SUCCESS_MESSAGE           = "SSE客户端已注册"
	SSE_UNREGISTER_SUCCESS_MESSAGE         = "SSE客户端已注销"
	SSE_SEND_SUCCESS_MESSAGE               = "SSE通知已发送"
	SSE_SEND_FAIL_WARNING_MESSAGE          = "无法发送SSE通知，通道已满"
	SSE_CLIENT_NOT_FOUND_WARNING_MESSAGE   = "SSE客户端未找到"
	SSE_BROADCAST_SUCCESS_MESSAGE          = "广播消息已发送"
	SSE_BROADCAST_FAIL_WARNING_MESSAGE     = "无法广播消息，通道已满"
	SSE_SEND_EMPTY_WARNING_MESSAGE         = "尝试发送空通知"
	SSE_SEND_EMPTY_MESSAGE_WARNING_MESSAGE = "尝试发送空的SSE消息"
	SSE_SERIALIZE_MESSAGE_ERROR_MESSAGE    = "序列化SSE消息错误"

	// 查询错误
	COLLECT_QUERY_ERROR = "收藏查询错误"
	FOCUS_QUERY_ERROR   = "关注查询错误"
	LIKE_QUERY_ERROR    = "点赞查询错误"

	// 初始化
	LOCAL_IPV4_ADDRESS_NOT_FOUND_ERROR       = "未找到本机可用的 IPv4 地址"
	ZERO_LOGGER_INIT_FAIL                    = "初始化日志失败: %v"
	ES_CLIENT_INIT_FAIL                      = "初始化 ES 客户端失败: %v"
	RABBITMQ_CONNECTION_INIT_FAIL            = "初始化 RabbitMQ 连接失败: %v"
	RABBITMQ_CONNECT_SUCCESS                 = "RabbitMQ 连接成功"
	RABBITMQ_CHANNEL_NOT_INITIALIZED_MESSAGE = "RabbitMQ 发布者未初始化"
	NACOS_CLIENT_INIT_FAIL                   = "初始化 Nacos 客户端失败: %v"
	NACOS_REGISTER_FAIL                      = "Nacos 注册失败: service=%s, address=%s:%d, group=%s, err=%v"
	REDIS_INIT_FAIL                          = "初始化 Redis 客户端失败: %v"
	REDIS_CONNECT_SUCCESS                    = "Redis 连接成功: %s:%d (DB: %d)"
	MYSQL_CLOSE_FAIL                         = "关闭 MySQL 连接失败: %v"
	REDIS_CLOSE_FAIL                         = "关闭 Redis 连接失败: %v"
	FASTAPI_WEIGHTS_FORMAT_ERROR             = "FastAPI 响应格式异常"
	SEARCH_WEIGHTS_FETCH_FAIL                = "获取搜索参数失败: %v"
	ENSURE_CHAT_MESSAGES_TABLE_FAIL          = "确保 chat_messages 表存在失败: %v"
	ENSURE_CHAT_MESSAGES_TABLE_SUCCESS       = "已确保 chat_messages 表存在"

	// 日志文件
	LOGGER_GET_WORKDIR_ERROR = "获取工作目录失败: %w"
	LOGGER_CREATE_DIR_ERROR  = "创建日志目录失败: %w"
	LOGGER_OPEN_FILE_ERROR   = "打开日志文件失败: %v"
	LOGGER_WRITE_FILE_ERROR  = "写入日志文件失败: %v"
	LOGGER_CLOSE_FILE_ERROR  = "关闭日志文件失败: %v"

	// 配置
	READ_CONFIG_FILE_ERROR  = "读取配置文件失败: %s, %v"
	PARSE_CONFIG_FILE_ERROR = "解析配置文件失败: %s, %v"
	CONFIG_DESCRIPTION      = "配置文件路径，默认为 etc/application.yaml"

	// go-zero 日志配置
	GOZERO_LOG_SETUP_FAIL = "初始化 go-zero 日志配置失败: %v"

	// 序列化/HTTP
	UNEXPECTED_STATUS_CODE = "异常状态码: %d, 响应内容: %s"

	// 服务发现/调用
	SERVICE_DISCOVERY_ERROR                = "服务发现失败"
	NO_AVAILABLE_SERVICE_INSTANCE          = "无可用服务实例"
	SERVICE_CALL_FAILED                    = "服务调用失败: %s"
	SERVICE_BUSINESS_ERROR_LOG             = "服务 %s 返回业务错误: code=%d, msg=%s"
	DOWNSTREAM_SERVICE_UNAVAILABLE_MESSAGE = "下游服务 %s 暂不可用，已触发熔断降级: %w"
	GRAPH_ENHANCE_CALL_FAILED              = "图谱增强服务调用失败: %w"
	GRAPH_ENHANCE_DEGRADE_LOG              = "图谱增强失败，降级为ES搜索: keyword=%s, userId=%d, articleCount=%d, err=%v"
	VECTOR_ENHANCE_CALL_FAILED             = "向量增强服务调用失败: %w"
	VECTOR_ENHANCE_DEGRADE_LOG             = "向量增强失败，降级为ES搜索: keyword=%s, userId=%d, articleCount=%d, err=%v"
	SCRIPT_PARAMS_FETCH_DEGRADE_LOG        = "获取脚本参数名映射失败，降级使用weightKey作为参数名: %v"

	// 用户日志
	RECORD_DURATION_MESSAGE    = "%s %s 使用了%dms"
	USER_LOG_MESSAGE           = "用户%d:%s %s %s: %s"
	ANONYMOUS_USER_LOG_MESSAGE = "匿名用户 %s %s: %s"

	// 搜索校验字段名
	SEARCH_START_TIME_FIELD = "开始时间"
	SEARCH_END_TIME_FIELD   = "结束时间"

	// API日志
	SERIALIZE_API_LOG_FAIL_MESSAGE = "序列化 API 日志消息失败: %v"
	SEND_API_LOG_FAIL_MESSAGE      = "发送 API 日志到队列失败: %v"
	SEND_API_LOG_SUCCESS_MESSAGE   = "API 日志已发送到队列"
	API_LOG_USER_ID_FIELD          = "用户ID"
	API_LOG_USERNAME_FIELD         = "用户名"
	API_LOG_SESSION_ID_FIELD       = "会话ID"
	API_LOG_REQUEST_METHOD_FIELD   = "请求方法"
	API_LOG_REQUEST_PATH_FIELD     = "请求路径"
	API_LOG_DESCRIPTION_FIELD      = "描述"
	API_LOG_QUERY_PARAMS_FIELD     = "查询参数"
	API_LOG_REQUEST_BODY_FIELD     = "请求体"
	API_LOG_QUERY_PARAMS_PREFIX    = "查询参数: "
	API_LOG_REQUEST_BODY_PREFIX    = "请求体: "
	LOG_TRUNCATED_SUFFIX           = "...[截断]"
	API_LOG_WEBSOCKET_CONNECTION   = "WebSocket连接"
	API_LOG_SSE_CONNECTION         = "SSE连接"

	// ES同步
	ES_CLIENT_NOT_INITIALIZED_MESSAGE     = "ES 客户端未初始化，跳过 ES 同步"
	ES_BULK_SYNC_ERROR_MESSAGE            = "ES批量同步错误"
	ES_SYNC_HAS_FAILURES_MESSAGE          = "ES同步有失败项"
	ES_SYNC_FAILURE_DETAILS_MESSAGE       = "ES同步失败: %+v"
	ES_SYNC_BATCH_COMPLETED_MESSAGE       = "第 %d 批同步完成，新增 %d 条，更新 %d 条"
	ES_INCREMENTAL_SYNC_COMPLETED_MESSAGE = "ES 增量同步完成，新增 %d 条，更新 %d 条，删除 %d 条"
	TASK_SYNC_ES_STARTED_MESSAGE          = "[定时任务] 开始同步文章到 ElasticSearch"
	TASK_SYNC_ES_COMPLETED_MESSAGE        = "[定时任务] 同步成功"
	TASK_SYNC_ES_FAILED_MESSAGE           = "[定时任务] 注册同步任务失败：%v"
	TASK_SCHEDULER_STARTED_MESSAGE        = "[定时任务] 已启动"
	NO_PUBLISHED_ARTICLES_TO_SYNC_MESSAGE = "没有已发布的文章可同步"
	INDEX_CHECK_ERROR_MESSAGE             = "索引判断错误"
	INDEX_CREATION_ERROR_MESSAGE          = "索引创建错误"

	// 内部令牌日志
	INTERNAL_TOKEN_HEADER_MISSING_LOG   = "[内部令牌验证] 缺少 %s 请求头，路径: %s"
	INTERNAL_TOKEN_VALIDATE_FAIL_LOG    = "[内部令牌验证] 令牌验证失败: %v, 路径: %s"
	INTERNAL_TOKEN_EXPIRED_LOG          = "[内部令牌验证] 令牌已过期，路径: %s"
	INTERNAL_TOKEN_SERVICE_MISMATCH_LOG = "[内部令牌验证] 服务名不匹配，期望: %s, 实际: %s, 路径: %s"
	INTERNAL_TOKEN_VALIDATE_SUCCESS_LOG = "[内部令牌验证] 验证成功，用户ID: %d, 服务: %s, 路径: %s"

	// 异常/错误消息
	BUSINESS_ERROR_MESSAGE          = "业务异常错误: %s\n错误详情: %s\n%s"
	STACK_ERROR_MESSAGE             = "堆栈错误信息: %v\n%s"
	SAFE_GO_PANIC_RECOVERED_MESSAGE = "异步任务 %s 执行时发生 panic，已自动恢复: %v\n堆栈信息:\n%s"
	UNIFIED_ERROR_RESPONSE_MESSAGE  = "服务器错误"
	SEARCH_HISTORY_FAIL             = "获取搜索历史失败"
	USER_ID_LESS                    = "缺少用户ID"

	// 远程调用响应解析错误
	RESPONSE_DATA_EMPTY          = "响应数据为空"
	RESPONSE_DATA_SERIALIZE      = "序列化响应数据失败: %w"
	RESPONSE_DATA_DESERIALIZE    = "反序列化响应数据失败: %w"
	BATCH_QUERY_USER_FAIL        = "批量查询用户失败: %v"
	BATCH_QUERY_SUBCATEGORY_FAIL = "批量查询子分类失败: %v"

	// Redis 分布式锁
	REDIS_LOCK_ACQUIRE_ERROR   = "获取分布式锁错误: %v"
	REDIS_LOCK_ACQUIRE_FAIL    = "[分布式锁] 获取锁失败，跳过本次执行，key: %s"
	REDIS_LOCK_ACQUIRE_SUCCESS = "[分布式锁] 获取锁成功，key: %s"
	REDIS_LOCK_RELEASE_ERROR   = "释放分布式锁错误: %v"
	REDIS_LOCK_RELEASE_FAIL    = "[分布式锁] 释放锁失败，key: %s"
	REDIS_LOCK_RELEASE_SUCCESS = "[分布式锁] 释放锁成功，key: %s"

	// Redis 实时消息
	REDIS_REALTIME_SUBSCRIBE_ERROR              = "订阅 Redis 实时消息失败: %v"
	REDIS_REALTIME_PUBLISH_ERROR                = "发布 Redis 实时消息失败: %v"
	REDIS_REALTIME_MESSAGE_ERROR                = "处理 Redis 实时消息失败: %v"
	REDIS_REALTIME_BUS_NOT_INITIALIZED_ERROR    = "Redis 实时消息总线未初始化"
	REDIS_REALTIME_INVALID_MESSAGE_FORMAT_ERROR = "处理 Redis 实时消息失败: 消息格式无效"
	MARK_MESSAGE_READ_ERROR                     = "标记聊天消息已读失败: %v"

	// API日志操作描述（ApplyApiLog 的接口描述参数）
	API_LOG_TEST_GOZERO_SERVICE      = "测试GoZero服务"
	API_LOG_MANUAL_SYNC_ES_TASK      = "手动触发同步ES任务"
	API_LOG_GET_SEARCH_HISTORY       = "获取搜索历史"
	API_LOG_SEARCH_ARTICLES          = "搜索文章"
	API_LOG_GET_UNREAD_MESSAGE_COUNT = "获取未读消息数"
	API_LOG_GET_ALL_UNREAD_COUNTS    = "获取所有未读消息数"
	API_LOG_GET_QUEUE_STATUS         = "获取队列状态"
	API_LOG_LEAVE_QUEUE              = "离开队列"
	API_LOG_GET_CHAT_HISTORY         = "获取聊天历史"
	API_LOG_SEND_MESSAGE             = "发送消息"
	API_LOG_JOIN_QUEUE               = "加入队列"
	API_LOG_SQL_TOOLS_GET_TABLES     = "获取SQL工具表结构信息"
	API_LOG_SQL_TOOLS_EXECUTE_QUERY  = "执行SQL工具只读查询"

	// Swagger
	SWAGGER_PAGE_FETCH_FAIL = "获取 Swagger 页面失败"

	// FastAPI 客户端错误描述
	FASTAPI_ARTICLE_IDS_EMPTY            = "文章ID列表为空"
	FASTAPI_ARTICLE_IDS_OR_KEYWORD_EMPTY = "文章ID列表为空或关键词为空"

	// 异步任务描述（SafeGo）
	SAFE_GO_SYNC_ES_DATA = "同步ES数据"

	// ===== SQL 工具安全约束消息 =====
	SQL_TOOLS_QUERY_EMPTY         = "SQL查询语句不能为空"
	SQL_TOOLS_FORBIDDEN_STATEMENT = "安全限制：只允许执行只读查询（SELECT/WITH/SHOW/DESC/DESCRIBE/EXPLAIN）"
	SQL_TOOLS_MULTIPLE_STATEMENTS = "安全限制：禁止执行多条SQL语句"
	SQL_TOOLS_LIMIT_REQUIRED      = "安全限制：SQL查询必须包含LIMIT子句"
	SQL_TOOLS_LIMIT_EXCEEDED      = "安全限制：LIMIT超过最大限制100"
	SQL_TOOLS_TABLE_NOT_ALLOWED   = "安全限制：表 '%s' 不在白名单内"
	SQL_TOOLS_QUERY_FAILED        = "执行SQL查询失败"
	SQL_TOOLS_MYSQL_UNINITIALIZED = "MySQL 连接未初始化"
	SQL_TOOLS_MYSQL_DRIVER        = "mysql"
)
