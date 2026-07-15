package constants

// 消息类常量 — 日志消息、用户提示、状态描述
const (
	// 测试/启动
	TEST_MESSAGE      = "Hello,I am GoZero!"
	SERVER_START_MESSAGE    = "服务启动于 %s:%d..."
	SWAGGER_DOCS_MESSAGE    = "Swagger 文档地址 http://%s:%d/swagger/index.html"
	INIT_IP                = "127.0.0.1"
	SERVER_START_SUCCESS    = "服务启动成功"
	GET_SWAGGER_FAIL        = "获取 Swagger 文档失败"

	// Nacos
	REGISTER_NACOS_DEV_MODE_MESSAGE = "SERVER_MODE=dev，Nacos 注册统一使用 127.0.0.1"

	// 搜索
	SEARCH_ERR              = "文章搜索错误"
	SEARCH_MSG              = "发起了文章搜索"
	SEARCH_EXECUTION_ERROR  = "搜索执行错误"
	ARTICLE_SEARCH_SUCCESS  = "文章搜索成功"

	// WebSocket
	WS_SEND_SUCCESS               = "消息 %d 通过WebSocket发送成功，已标记为已读"
	WS_SEND_FAIL                  = "用户 %s 不在线，消息 %d 已保存为未读"
	WS_SERIALIZE_MESSAGE_ERROR    = "序列化WebSocket消息失败: %v"
	MESSAGE_SEND_ERROR            = "消息发送失败"
	MARK_READ_FAIL                = "标记消息 %d 为已读失败"
	USER_JOINED_QUEUE             = "用户 %s 已加入聊天队列"
	USER_LEFT_QUEUE               = "用户 %s 已离开聊天队列"
	USER_IN_QUEUE_NOT_CONNECTED   = "用户 %s 在队列中但没有WebSocket连接，无法发送实时消息"
	WS_ERROR                      = "WebSocket 错误: %v"
	PARSE_MESSAGE_FAIL            = "解析消息失败: %v"
	WEBSOCKET_CONNECTION_ESTABLISHED_MESSAGE = "WebSocket 连接已建立"
	WS_CONNECT_FAIL               = "WebSocket连接失败"
	WS_WRITE_MESSAGE_FAIL         = "WebSocket 写消息失败: %v"
	USER_CONNECTED                = "joined"
	USER_ALREADY_IN_QUEUE         = "already_in_queue"
	USER_DISCONNECTED             = "left"
	USER_NOT_IN_QUEUE             = "not_in_queue"
	HEARTBEAT_MESSAGE             = "ping"
	HEARTBEAT_RESPONSE            = "pong"

	// SSE
	SSE_REGISTER_SUCCESS              = "SSE客户端 %s 已注册"
	SSE_UNREGISTER_SUCCESS            = "SSE客户端 %s 已注销"
	SSE_SEND_EMPTY_WARNING            = "尝试发送空通知给用户 %s"
	SSE_CLIENT_NOT_FOUND_WARNING      = "用户 %s 的SSE客户端未找到"
	SSE_SEND_SUCCESS                  = "SSE通知已发送给用户 %s"
	SSE_SEND_FAIL_WARNING             = "无法发送SSE通知给用户 %s,通道已满"
	SSE_BROADCAST_SUCCESS             = "广播消息已发送给用户 %s"
	SSE_BROADCAST_FAIL_WARNING        = "无法广播消息给用户 %s，通道已满"
	SSE_SEND_EMPTY_MESSAGE_WARNING    = "尝试发送空的SSE消息"
	SSE_SERIALIZE_MESSAGE_ERROR       = "序列化SSE消息错误: %v"
	SSE_SERIALIZE_MESSAGE_EMPTY       = "序列化后的SSE消息为null"
	SSE_CONNECTION_ESTABLISHED_MESSAGE = "SSE 连接已建立"
	SSE_HEARTBEAT_WRITE_FAIL          = "SSE心跳写入失败: "
	EMPTY_SSE                         = "跳过空的SSE消息"
	SSE_WRITE_FAIL                    = "SSE写入失败: "
	SSE_HEARTBEAT                     = ": heartbeat\n\n"

	// 聊天
	CREATE_MESSAGE_ERROR       = "消息创建错误"
	GET_HISTORY_MESSAGE_ERROR  = "获取消息历史错误"
	GET_UNREAD_COUNT_ERROR     = "获取两个用户间未读消息数错误"
	GET_ALL_UNREAD_COUNTS_ERROR = "获取用户与其他所有人的未读消息数错误"
	GET_UNREAD_COUNT_MESSAGE_ERROR = "获取未读消息数失败: %v"
	CHAT_MESSAGE_SEND_SUCCESS  = "聊天消息发送成功"
	GET_CHAT_HISTORY_SUCCESS   = "获取聊天历史成功"
	GET_UNREAD_COUNT_SUCCESS   = "获取未读消息数成功"
	GET_ALL_UNREAD_COUNTS_SUCCESS = "获取所有未读消息数成功"
	JOIN_QUEUE_SUCCESS         = "加入聊天队列成功"
	LEAVE_QUEUE_SUCCESS        = "离开聊天队列成功"
	GET_QUEUE_STATUS_SUCCESS   = "获取队列状态成功"
	USER_JOINED_QUEUE_MESSAGE  = "用户已加入聊天队列"
	USER_LEFT_QUEUE_MESSAGE    = "用户已离开聊天队列"
	USER_IN_QUEUE_NOT_CONNECTED_WARNING = "用户在队列中但没有WebSocket连接，无法发送实时消息"
	SSE_REGISTER_SUCCESS_MESSAGE = "SSE客户端已注册"
	SSE_UNREGISTER_SUCCESS_MESSAGE = "SSE客户端已注销"
	SSE_SEND_SUCCESS_MESSAGE = "SSE通知已发送"
	SSE_SEND_FAIL_WARNING_MESSAGE = "无法发送SSE通知，通道已满"
	SSE_CLIENT_NOT_FOUND_WARNING_MESSAGE = "SSE客户端未找到"
	SSE_BROADCAST_SUCCESS_MESSAGE = "广播消息已发送"
	SSE_BROADCAST_FAIL_WARNING_MESSAGE = "无法广播消息，通道已满"
	SSE_SEND_EMPTY_WARNING_MESSAGE = "尝试发送空通知"
	SSE_SEND_EMPTY_MESSAGE_WARNING_MESSAGE = "尝试发送空的SSE消息"
	SSE_SERIALIZE_MESSAGE_ERROR_MESSAGE = "序列化SSE消息错误"

	// 查询错误
	ARTICLE_QUERY_ERROR   = "文章查询错误"
	CATEGORY_QUERY_ERROR  = "分类查询错误"
	COLLECT_QUERY_ERROR   = "收藏查询错误"
	FOCUS_QUERY_ERROR     = "关注查询错误"
	LIKE_QUERY_ERROR      = "点赞查询错误"
	QUERY_USER_ERROR      = "查询用户 %d 失败: %v"
	QUERY_SUBCATEGORY_ERROR = "查询子分类 %d 失败: %v"
	QUERY_CATEGORY_ERROR  = "查询分类 %d 失败: %v"

	// 初始化
	GET_WORKING_DIR_ERROR      = "获取当前工作目录失败"
	LOCAL_IPV4_ADDRESS_NOT_FOUND_ERROR = "未找到本机可用的 IPv4 地址"
	CREATE_LOG_DIR_ERROR       = "创建日志目录失败"
	ZERO_LOGGER_INIT_FAIL      = "初始化日志失败: %v"
	GORM_INIT_FAIL             = "初始化 Gorm 失败: %v"
	ES_CLIENT_INIT_FAIL        = "初始化 ES 客户端失败: %v"
	RABBITMQ_CONNECTION_INIT_FAIL = "初始化 RabbitMQ 连接失败: %v"
	RABBITMQ_CONNECT_SUCCESS   = "RabbitMQ 连接成功"
	RABBITMQ_CHANNEL_NOT_INITIALIZED_MESSAGE = "RabbitMQ 发布者未初始化"
	MONGODB_CONNECTION_INIT_FAIL = "初始化 MongoDB 连接失败: %v"
	MONGODB_PING_FAIL          = "MongoDB 心跳检测失败: %v"
	NACOS_CLIENT_INIT_FAIL     = "初始化 Nacos 客户端失败: %v"
	NACOS_REGISTER_FAIL        = "Nacos 注册失败: service=%s, address=%s:%d, group=%s, err=%v"
	REDIS_INIT_FAIL            = "初始化 Redis 客户端失败: %v"
	REDIS_CONNECT_SUCCESS      = "Redis 连接成功: %s:%d (DB: %d)"
	GORM_IS_NIL_MESSAGE        = "GORM DB 对象未初始化"

	// 日志文件
	OPEN_LOG_FILE_ERROR  = "打开日志文件失败"
	WRITE_LOG_FILE_ERROR = "写入日志文件失败"
	LOGGER_GET_WORKDIR_ERROR = "获取工作目录失败: %w"
	LOGGER_CREATE_DIR_ERROR  = "创建日志目录失败: %w"
	LOGGER_OPEN_FILE_ERROR   = "打开日志文件失败: %v"
	LOGGER_WRITE_FILE_ERROR  = "写入日志文件失败: %v"

	// 配置
	READ_CONFIG_FILE_ERROR  = "读取配置文件失败: %s, %v"
	PARSE_CONFIG_FILE_ERROR = "解析配置文件失败: %s, %v"
	CONFIG_DESCRIPTION      = "配置文件路径，默认为 etc/application.yaml"

	// 建表
	AUTO_CREATE_TABLE_FAIL    = "自动创建 chat_messages 表失败: %v"
	AUTO_CREATE_TABLE_SUCCESS = "自动创建 chat_messages 表成功"

	// 序列化/HTTP
	JSON_SERIALIZATION_ERROR = "JSON序列化失败"
	UNEXPECTED_STATUS_CODE   = "异常状态码: %d, 响应内容: %s"

	// 服务发现/调用
	SERVICE_DISCOVERY_ERROR          = "服务发现失败"
	NO_AVAILABLE_SERVICE_INSTANCE    = "无可用服务实例"
	SERVICE_CALL_FAILED              = "服务调用失败: %s"
	SERVICE_BUSINESS_ERROR_LOG       = "服务 %s 返回业务错误: code=%d, msg=%s"
	DOWNSTREAM_SERVICE_UNAVAILABLE_MESSAGE = "下游服务 %s 暂不可用，已触发熔断降级: %w"
	GRAPH_ENHANCE_CALL_FAILED        = "图谱增强服务调用失败: %w"
	GRAPH_ENHANCE_RESPONSE_FORMAT_ERROR = "图谱增强响应格式异常"
	GRAPH_ENHANCE_DEGRADE_LOG        = "图谱增强失败，降级为ES搜索: keyword=%s, userId=%d, articleCount=%d, err=%v"
	VECTOR_ENHANCE_CALL_FAILED       = "向量增强服务调用失败: %w"
	VECTOR_ENHANCE_RESPONSE_FORMAT_ERROR = "向量增强响应格式异常"
	VECTOR_ENHANCE_DEGRADE_LOG       = "向量增强失败，降级为ES搜索: keyword=%s, userId=%d, articleCount=%d, err=%v"
	SPRING_CALL_FAILED               = "调用 Spring 服务失败: %w"
	NESTJS_CALL_FAILED               = "调用 NestJS 服务失败: %w"

	// 用户日志
	RECORD_DURATION_MESSAGE    = "%s %s 使用了%dms"
	USER_LOG_MESSAGE           = "用户%d:%s %s %s: %s"
	ANONYMOUS_USER_LOG_MESSAGE = "匿名用户 %s %s: %s"

	// API日志
	SERIALIZE_API_LOG_FAIL_MESSAGE               = "序列化 API 日志消息失败: %v"
	SEND_API_LOG_FAIL_MESSAGE                     = "发送 API 日志到队列失败: %v"
	SEND_API_LOG_SUCCESS_MESSAGE                  = "API 日志已发送到队列"
	SEND_API_LOG_RABBITMQ_NOT_INITIALIZED_MESSAGE = "RabbitMQ 未初始化，无法发送 API 日志"
	API_LOG_SEND_FAIL_MESSAGE                     = "[API日志发送失败] 队列: api-log-queue, 错误: %v"
	API_LOG_SEND_SUCCESS_MESSAGE_LONG             = "[API日志发送成功] 队列: api-log-queue, 消息: %s"

	// ES同步
	ES_CLIENT_NOT_INITIALIZED_MESSAGE             = "ES 客户端未初始化，跳过 ES 同步"
	BULK_FETCH_ARTICLE_RATINGS_COMPLETED_MESSAGE  = "批量获取 %d 篇文章的评分信息完成"
	ES_BULK_SYNC_ERROR_MESSAGE                    = "ES批量同步错误"
	ES_SYNC_HAS_FAILURES_MESSAGE                  = "ES同步有失败项"
	ES_SYNC_FAILURE_DETAILS_MESSAGE               = "ES同步失败: %+v"
	ES_SYNC_BATCH_SUBMISSION_COMPLETED_MESSAGE    = "第 %d/%d 批提交完成，共 %d 条记录"
	ES_SYNC_BATCH_COMPLETED_MESSAGE               = "第 %d 批同步完成，新增 %d 条，更新 %d 条"
	ES_INCREMENTAL_SYNC_COMPLETED_MESSAGE         = "ES 增量同步完成，新增 %d 条，更新 %d 条，删除 %d 条"
	TASK_SYNC_ES_STARTED_MESSAGE                  = "[定时任务] 开始同步文章到 ElasticSearch"
	TASK_SYNC_ES_COMPLETED_MESSAGE                = "[定时任务] 同步成功"
	TASK_SYNC_ES_FAILED_MESSAGE                   = "[定时任务] 注册同步任务失败：%v"
	TASK_SCHEDULER_STARTED_MESSAGE                = "[定时任务] 已启动"
	BULK_FETCH_ARTICLE_LIKES_COLLECTS_COMPLETED_MESSAGE = "批量获取 %d 篇文章的点赞和收藏信息完成"
	BULK_FETCH_AUTHOR_FOLLOWS_COMPLETED_MESSAGE   = "批量获取 %d 个作者的关注信息完成"
	NO_PUBLISHED_ARTICLES_TO_SYNC_MESSAGE         = "没有已发布的文章可同步"
	INDEX_CHECK_ERROR_MESSAGE                     = "索引判断错误"
	INDEX_CREATION_ERROR_MESSAGE                  = "索引创建错误"
	INDEX_DELETION_ERROR_MESSAGE                  = "索引删除错误"

	// 内部令牌日志
	INTERNAL_TOKEN_HEADER_MISSING_LOG   = "[内部令牌验证] 缺少 %s 请求头，路径: %s"
	INTERNAL_TOKEN_EMPTY_LOG            = "[内部令牌验证] 令牌为空，路径: %s"
	INTERNAL_TOKEN_VALIDATE_FAIL_LOG    = "[内部令牌验证] 令牌验证失败: %v, 路径: %s"
	INTERNAL_TOKEN_EXPIRED_LOG          = "[内部令牌验证] 令牌已过期，路径: %s"
	INTERNAL_TOKEN_SERVICE_MISMATCH_LOG = "[内部令牌验证] 服务名不匹配，期望: %s, 实际: %s, 路径: %s"
	INTERNAL_TOKEN_VALIDATE_SUCCESS_LOG = "[内部令牌验证] 验证成功，用户ID: %d, 服务: %s, 路径: %s"

	// 异常/错误消息
	BUSINESS_ERROR_MESSAGE         = "业务异常错误: %s\n错误详情: %s\n%s"
	STACK_ERROR_MESSAGE            = "堆栈错误信息: %v\n%s"
	SAFE_GO_PANIC_RECOVERED_MESSAGE = "异步任务 %s 执行时发生 panic，已自动恢复: %v\n堆栈信息:\n%s"
	UNIFIED_ERROR_RESPONSE_MESSAGE = "服务器错误"
	PARSE_ERR                      = "解析错误"
	SEARCH_HISTORY_FAIL            = "获取搜索历史失败"
	USER_ID_LESS                   = "缺少用户ID"

	// Redis 分布式锁
	REDIS_LOCK_ACQUIRE_ERROR   = "获取分布式锁错误: %v"
	REDIS_LOCK_ACQUIRE_FAIL    = "[分布式锁] 获取锁失败，跳过本次执行，key: %s"
	REDIS_LOCK_ACQUIRE_SUCCESS = "[分布式锁] 获取锁成功，key: %s"
	REDIS_LOCK_RELEASE_ERROR   = "释放分布式锁错误: %v"
	REDIS_LOCK_RELEASE_FAIL    = "[分布式锁] 释放锁失败，key: %s"
	REDIS_LOCK_RELEASE_SUCCESS = "[分布式锁] 释放锁成功，key: %s"
)

// NOTE: 命名冲突避免 — API_LOG_SEND_SUCCESS_MESSAGE 和 API_LOG_SEND_SUCCESS_MESSAGE_LONG
// 原始文件中分别对应 SEND_API_LOG_SUCCESS_MESSAGE(无前缀) 和 API_LOG_SEND_SUCCESS_MESSAGE([前缀])
// 两者语义不同: 前者是 "已发送到队列", 后者是 "[API日志发送成功] 队列: api-log-queue, 消息: %s"
