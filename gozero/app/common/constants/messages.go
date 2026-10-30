package constants

const (
	// ===== 用户身份校验 =====

	// 缺少当前登录用户身份的用户提示
	USER_IDENTITY_MISSING = "缺少当前登录用户身份"
	// 只能访问本人数据或使用管理员权限的用户提示
	SELF_OR_ADMIN_REQUIRED = "只能访问本人数据，或使用管理员权限"
	// 管理员权限校验失败的日志消息
	ADMIN_PERMISSION_CHECK_FAILED = "管理员权限校验失败"
)

// 消息类常量 — 日志消息、用户提示、状态描述
const (
	// ===== 测试/启动 =====

	// 服务连通性测试返回的固定消息
	TEST_MESSAGE = "Hello,I am GoZero!"
	// 服务启动地址与端口的日志消息
	SERVER_START_MESSAGE = "服务启动于 %s:%d..."
	// 运行模式的日志消息
	SERVER_MODE_MESSAGE = "运行模式: %s"
	// Swagger 文档地址的日志消息
	SWAGGER_DOCS_MESSAGE = "Swagger 文档地址 http://%s:%d/swagger/index.html"
	// 服务启动成功的日志消息
	SERVER_START_SUCCESS = "服务启动成功"
	// 服务启动失败的日志消息
	SERVER_START_FAIL = "服务启动失败: %v"
	// 获取 Swagger 文档失败的日志消息
	GET_SWAGGER_FAIL = "获取 Swagger 文档失败"

	// ===== 基础设施降级 =====

	// MySQL 配置缺失时以无连接模式运行的降级消息
	MYSQL_CONFIG_MISSING_DEGRADE = "MySQL 配置缺失(host/port/username/dbname 为空)，服务将以无 MySQL 连接模式降级运行"
	// 标准库 MySQL 连接不可用导致 SQL 工具降级的消息
	RAW_MYSQL_CONFIG_MISSING_DEGRADE = "MySQL 配置缺失，标准库 MySQL 连接不可用，SQL 工具动态查询能力降级"
	// ElasticSearch 地址未配置导致搜索不可用的降级消息
	ES_CONFIG_MISSING_DEGRADE = "ElasticSearch 地址未配置，搜索相关功能将不可用"
	// RabbitMQ 地址未配置导致 API 日志投递不可用的降级消息
	RABBITMQ_CONFIG_MISSING_DEGRADE = "RabbitMQ 地址未配置，API 日志投递功能将不可用"
	// Redis 地址未配置导致分布式锁与实时广播不可用的降级消息
	REDIS_CONFIG_MISSING_DEGRADE = "Redis 地址未配置，分布式锁与实时广播功能将不可用"
	// Nacos 地址未配置导致服务发现不可用的降级消息
	NACOS_CONFIG_MISSING_DEGRADE = "Nacos 地址未配置，服务发现、注册与服务间调用将不可用"

	// ===== Nacos =====

	// 注册到 Nacos 成功的日志消息
	NACOS_REGISTERED_MESSAGE = "注册到 Nacos 成功: %s:%d"
	// Nacos 注册失败后重试的告警消息
	NACOS_REGISTER_RETRY_WARNING = "Nacos 注册失败(第 %d/%d 次)，稍后重试: %v"
	// Nacos 注册重试耗尽转为后台补注册的告警消息
	NACOS_REGISTER_DEGRADE_WARNING = "Nacos 注册重试耗尽，服务继续启动并转入后台补注册，注册成功前网关无法发现该实例"
	// Nacos 后台补注册仍失败的告警消息
	NACOS_REGISTER_BACKGROUND_GIVE_UP_ERROR = "Nacos 后台补注册仍未成功，实例未注册到注册中心: service=%s, address=%s:%d"
	// 未解析到可注册 IP 时跳过注册的告警消息
	NACOS_REGISTER_IP_MISSING_DEGRADE = "未解析到可注册的 IP，已跳过 Nacos 实例注册"
	// Nacos SDK 目录不可用的告警消息
	NACOS_DIR_UNUSABLE_WARNING = "Nacos 目录不可用，路径: %s, 原因: %v"
	// Nacos SDK 目录不可写时回退的告警消息
	NACOS_DIR_FALLBACK_WARNING = "Nacos 目录 %s 不可写，已回退到 %s"
	// Nacos SDK 全部目录不可写的错误消息
	NACOS_DIR_UNAVAILABLE_ERROR = "Nacos 的 %s 目录均不可写，Nacos SDK 将无法写入本地文件: %v"
	// 加载 .env 文件失败的错误消息
	GODOTENV_LOAD_FAIL = "加载.env文件失败: %v"

	// ===== 错误 =====

	// 内部令牌密钥为空的错误消息
	INTERNAL_TOKEN_SECRET_NOT_NULL = "内部服务令牌密钥不能为空"
	// 内部令牌初始化失败的错误消息
	INTERNAL_TOKEN_INIT_FAIL = "内部服务令牌初始化失败: %v"
	// 内部令牌未初始化的错误消息
	INTERNAL_TOKEN_NOT_INITIALIZED = "内部服务令牌未初始化"
	// 请求头缺少内部令牌的错误消息
	INTERNAL_TOKEN_MISSING = "缺少必需的内部服务令牌请求头"
	// 内部令牌无效的错误消息
	INTERNAL_TOKEN_INVALID = "内部服务令牌无效"
	// 内部令牌已过期的错误消息
	INTERNAL_TOKEN_EXPIRED = "内部服务令牌已过期"
	// 内部令牌服务名不匹配的错误消息
	SERVICE_NAME_MISMATCH = "服务名称不匹配"

	// ===== 搜索 =====

	// 文章搜索错误的日志消息
	SEARCH_ERR = "文章搜索错误"
	// 发起文章搜索的日志消息
	SEARCH_MSG = "发起了文章搜索"
	// 搜索执行错误的日志消息
	SEARCH_EXECUTION_ERROR = "搜索执行错误"
	// 文章搜索成功的日志消息
	ARTICLE_SEARCH_SUCCESS = "文章搜索成功"

	// ===== WebSocket =====

	// WebSocket 消息发送成功并标记已读的日志消息
	WS_SEND_SUCCESS = "消息 %d 通过WebSocket发送成功，已标记为已读"
	// 用户不在线时消息保存为未读的日志消息
	WS_SEND_FAIL = "用户 %d 不在线，消息 %d 已保存为未读"
	// 序列化 WebSocket 消息失败的日志消息
	WS_SERIALIZE_MESSAGE_ERROR = "序列化WebSocket消息失败: %v"
	// 发送 WebSocket 关闭帧失败的日志消息
	WS_CLOSE_FRAME_SEND_FAIL = "发送WebSocket关闭帧失败: %v"
	// 序列化 WebSocket 心跳响应失败的日志消息
	WS_HEARTBEAT_RESPONSE_FAIL = "序列化WebSocket心跳响应失败: %v"
	// 消息发送失败的日志消息
	MESSAGE_SEND_ERROR = "消息发送失败"
	// 标记消息已读失败的日志消息
	MARK_READ_FAIL = "标记消息 %d 为已读失败"
	// WebSocket 错误的日志消息
	WS_ERROR = "WebSocket 错误: %v"
	// 解析 WebSocket 消息失败的日志消息
	PARSE_MESSAGE_FAIL = "解析消息失败: %v"
	// WebSocket 连接已建立的日志消息
	WEBSOCKET_CONNECTION_ESTABLISHED_MESSAGE = "WebSocket 连接已建立"
	// WebSocket 连接失败的日志消息
	WS_CONNECT_FAIL = "WebSocket连接失败"
	// WebSocket 写消息失败的日志消息
	WS_WRITE_MESSAGE_FAIL = "WebSocket 写消息失败: %v"
	// WebSocket 入队成功的事件类型
	USER_CONNECTED = "joined"
	// 用户已在队列中的事件类型
	USER_ALREADY_IN_QUEUE = "already_in_queue"
	// WebSocket 离开队列的事件类型
	USER_DISCONNECTED = "left"
	// 用户不在队列中的事件类型
	USER_NOT_IN_QUEUE = "not_in_queue"
	// 客户端心跳请求的类型字面量
	HEARTBEAT_MESSAGE = "ping"
	// 服务端心跳响应的类型字面量
	HEARTBEAT_RESPONSE = "pong"
	// 客户端已读回执的类型字面量
	READ_RECEIPT_MESSAGE = "read"
	// 服务端已读确认的类型字面量
	READ_RECEIPT_ACK = "read_ack"
	// 已读回执缺少发送者或消息 ID 的提示
	WS_READ_RECEIPT_INVALID = "已读回执缺少有效的发送者或消息ID"
	// 处理 WebSocket 已读回执失败的日志消息
	WS_READ_RECEIPT_HANDLE_FAIL = "处理WebSocket已读回执失败: %v"
	// 发送 WebSocket 已读确认失败的日志消息
	WS_READ_RECEIPT_ACK_FAIL = "发送WebSocket已读确认失败"

	// ===== SSE =====

	// 序列化后的 SSE 消息为空的日志消息
	SSE_SERIALIZE_MESSAGE_EMPTY = "序列化后的SSE消息为null"
	// SSE 连接已建立的日志消息
	SSE_CONNECTION_ESTABLISHED_MESSAGE = "SSE 连接已建立"
	// SSE 心跳写入失败的日志消息
	SSE_HEARTBEAT_WRITE_FAIL = "SSE心跳写入失败: "
	// 收到空 SSE 消息的日志消息
	EMPTY_SSE = "跳过空的SSE消息"
	// SSE 写入失败的日志消息
	SSE_WRITE_FAIL = "SSE写入失败: "
	// SSE 心跳帧内容
	SSE_HEARTBEAT = ": heartbeat\n\n"
	// SSE 初始消息写入失败的日志消息
	SSE_INIT_MESSAGE_SEND_FAIL = "SSE初始化消息写入失败: %v"

	// ===== 聊天 =====

	// 消息创建失败的日志消息
	CREATE_MESSAGE_ERROR = "消息创建错误"
	// 获取聊天历史失败的日志消息
	GET_HISTORY_MESSAGE_ERROR = "获取消息历史错误"
	// 获取指定用户未读消息数失败的日志消息
	GET_UNREAD_COUNT_ERROR = "获取两个用户间未读消息数错误"
	// 获取全部用户未读消息数失败的日志消息
	GET_ALL_UNREAD_COUNTS_ERROR = "获取用户与其他所有人的未读消息数错误"
	// 获取未读消息数失败的日志消息
	GET_UNREAD_COUNT_MESSAGE_ERROR = "获取未读消息数失败: %v"
	// 聊天消息发送成功的日志消息
	CHAT_MESSAGE_SEND_SUCCESS = "聊天消息发送成功"
	// 获取聊天历史成功的日志消息
	GET_CHAT_HISTORY_SUCCESS = "获取聊天历史成功"
	// 获取未读消息数成功的日志消息
	GET_UNREAD_COUNT_SUCCESS = "获取未读消息数成功"
	// 获取全部未读消息数成功的日志消息
	GET_ALL_UNREAD_COUNTS_SUCCESS = "获取所有未读消息数成功"
	// 加入匹配队列成功的日志消息
	JOIN_QUEUE_SUCCESS = "加入聊天队列成功"
	// 离开匹配队列成功的日志消息
	LEAVE_QUEUE_SUCCESS = "离开聊天队列成功"
	// 获取队列状态成功的日志消息
	GET_QUEUE_STATUS_SUCCESS = "获取队列状态成功"
	// 用户已加入匹配队列的提示
	USER_JOINED_QUEUE_MESSAGE = "用户已加入聊天队列"
	// 用户已离开匹配队列的提示
	USER_LEFT_QUEUE_MESSAGE = "用户已离开聊天队列"
	// 用户在队列但未建立 WebSocket 连接的告警
	USER_IN_QUEUE_NOT_CONNECTED_WARNING = "用户在队列中但没有WebSocket连接，无法发送实时消息"
	// SSE 客户端注册成功的日志消息
	SSE_REGISTER_SUCCESS_MESSAGE = "SSE客户端已注册"
	// SSE 客户端注销成功的日志消息
	SSE_UNREGISTER_SUCCESS_MESSAGE = "SSE客户端已注销"
	// SSE 通知发送成功的日志消息
	SSE_SEND_SUCCESS_MESSAGE = "SSE通知已发送"
	// 无法发送 SSE 通知的告警
	SSE_SEND_FAIL_WARNING_MESSAGE = "无法发送SSE通知，通道已满"
	// 未找到 SSE 客户端的告警
	SSE_CLIENT_NOT_FOUND_WARNING_MESSAGE = "SSE客户端未找到"
	// SSE 广播成功的日志消息
	SSE_BROADCAST_SUCCESS_MESSAGE = "广播消息已发送"
	// SSE 广播失败的告警
	SSE_BROADCAST_FAIL_WARNING_MESSAGE = "无法广播消息，通道已满"
	// 尝试发送空通知的告警
	SSE_SEND_EMPTY_WARNING_MESSAGE = "尝试发送空通知"
	// 尝试发送空 SSE 消息的告警
	SSE_SEND_EMPTY_MESSAGE_WARNING_MESSAGE = "尝试发送空的SSE消息"
	// 序列化 SSE 消息失败的日志消息
	SSE_SERIALIZE_MESSAGE_ERROR_MESSAGE = "序列化SSE消息错误"

	// ===== 查询错误 =====

	// 收藏查询错误的日志消息
	COLLECT_QUERY_ERROR = "收藏查询错误"
	// 关注查询错误的日志消息
	FOCUS_QUERY_ERROR = "关注查询错误"
	// 点赞查询错误的日志消息
	LIKE_QUERY_ERROR = "点赞查询错误"

	// ===== 响应解析错误 =====

	// 评论评分解析失败的日志消息
	COMMENT_SCORE_PARSE_ERROR = "评论评分解析错误"
	// 点赞数解析失败的日志消息
	LIKE_COUNT_PARSE_ERROR = "点赞数解析错误"
	// 收藏数解析失败的日志消息
	COLLECT_COUNT_PARSE_ERROR = "收藏数解析错误"
	// 粉丝数解析失败的日志消息
	FOCUS_COUNT_PARSE_ERROR = "粉丝数解析错误"

	// ===== 初始化 =====

	// 未找到可用 IPv4 地址的错误消息
	LOCAL_IPV4_ADDRESS_NOT_FOUND_ERROR = "未找到本机可用的 IPv4 地址"
	// 日志器初始化失败的日志消息
	ZERO_LOGGER_INIT_FAIL = "初始化日志失败: %v"
	// ES 客户端初始化失败的日志消息
	ES_CLIENT_INIT_FAIL = "初始化 ES 客户端失败: %v"
	// RabbitMQ 连接初始化失败的日志消息
	RABBITMQ_CONNECTION_INIT_FAIL = "初始化 RabbitMQ 连接失败: %v"
	// RabbitMQ 连接成功的日志消息
	RABBITMQ_CONNECT_SUCCESS = "RabbitMQ 连接成功"
	// RabbitMQ 通道未初始化的日志消息
	RABBITMQ_CHANNEL_NOT_INITIALIZED_MESSAGE = "RabbitMQ 发布者未初始化"
	// Nacos 客户端初始化失败的日志消息
	NACOS_CLIENT_INIT_FAIL = "初始化 Nacos 客户端失败: %v"
	// Nacos 实例注册失败的日志消息
	NACOS_REGISTER_FAIL = "Nacos 注册失败: service=%s, address=%s:%d, group=%s, err=%v"
	// Redis 客户端初始化失败的日志消息
	REDIS_INIT_FAIL = "初始化 Redis 客户端失败: %v"
	// Redis 连接成功的日志消息
	REDIS_CONNECT_SUCCESS = "Redis 连接成功: %s:%d (DB: %d)"
	// MySQL 连接关闭失败的日志消息
	MYSQL_CLOSE_FAIL = "关闭 MySQL 连接失败: %v"
	// Redis 连接关闭失败的日志消息
	REDIS_CLOSE_FAIL = "关闭 Redis 连接失败: %v"
	// FastAPI 响应格式异常的错误消息
	FASTAPI_RESPONSE_FORMAT_ERROR = "FastAPI 响应格式异常"
	// 确保 chat_messages 表存在失败的错误消息
	ENSURE_CHAT_MESSAGES_TABLE_FAIL = "确保 chat_messages 表存在失败: %v"
	// 确认 chat_messages 表就绪的日志消息
	ENSURE_CHAT_MESSAGES_TABLE_SUCCESS = "已确保 chat_messages 表存在"

	// ===== 日志文件 =====

	// 日志目录路径为空的错误消息
	LOGGER_PATH_EMPTY_ERROR = "日志目录路径不能为空，请检查 LOGS_PATH 环境变量配置"
	// 获取工作目录失败的错误消息
	LOGGER_GET_WORKDIR_ERROR = "获取工作目录失败: %w"
	// 创建日志目录失败的错误消息
	LOGGER_CREATE_DIR_ERROR = "创建日志目录失败: %w"
	// 打开日志文件失败的错误消息
	LOGGER_OPEN_FILE_ERROR = "打开日志文件失败: %v"
	// 写入日志文件失败的错误消息
	LOGGER_WRITE_FILE_ERROR = "写入日志文件失败: %v"
	// 关闭日志文件失败的错误消息
	LOGGER_CLOSE_FILE_ERROR = "关闭日志文件失败: %v"

	// ===== 配置 =====

	// 读取配置文件失败的错误消息
	READ_CONFIG_FILE_ERROR = "读取配置文件失败: %s, %v"
	// 解析配置文件失败的错误消息
	PARSE_CONFIG_FILE_ERROR = "解析配置文件失败: %s, %v"
	// 配置文件路径缺省值的说明
	CONFIG_DESCRIPTION = "配置文件路径，默认为 etc/application.yaml"

	// ===== go-zero 日志配置 =====

	// 初始化 go-zero 日志组件失败的错误消息
	GOZERO_LOG_SETUP_FAIL = "初始化 go-zero 日志配置失败: %v"

	// ===== 序列化/HTTP =====

	// 下游返回异常状态码的错误消息
	UNEXPECTED_STATUS_CODE = "异常状态码: %d, 响应内容: %s"

	// ===== 服务发现/调用 =====

	// 服务发现失败的日志消息
	SERVICE_DISCOVERY_ERROR = "服务发现失败"
	// 没有可用服务实例的降级消息
	NO_AVAILABLE_SERVICE_INSTANCE = "无可用服务实例"
	// 服务调用失败的降级消息
	SERVICE_CALL_FAILED = "服务调用失败: %s"
	// 下游返回业务错误的日志消息
	SERVICE_BUSINESS_ERROR_LOG = "服务 %s 返回业务错误: code=%d, msg=%s"
	// 下游服务暂不可用时的熔断降级消息
	DOWNSTREAM_SERVICE_UNAVAILABLE_MESSAGE = "下游服务 %s 暂不可用，已触发熔断降级: %w"
	// 图谱增强调用失败的错误消息
	GRAPH_ENHANCE_CALL_FAILED = "图谱增强服务调用失败: %w"
	// 图谱增强失败降级为纯 ES 检索的日志消息
	GRAPH_ENHANCE_DEGRADE_LOG = "图谱增强失败，降级为ES搜索: keyword=%s, userId=%d, articleCount=%d, err=%v"
	// 向量增强调用失败的错误消息
	VECTOR_ENHANCE_CALL_FAILED = "向量增强服务调用失败: %w"
	// 向量增强失败降级为纯 ES 检索的日志消息
	VECTOR_ENHANCE_DEGRADE_LOG = "向量增强失败，降级为ES搜索: keyword=%s, userId=%d, articleCount=%d, err=%v"
	// ES 脚本或权重的拉取失败后降级的日志消息
	SEARCH_SCRIPTS_FETCH_DEGRADE_LOG = "获取搜索脚本、权重与脚本参数名映射失败，降级为普通 ES 条件分页查询: script=%v, weights=%v, scriptParams=%v"
	// 召回窗口超出上限后退化为窗口内重排的日志消息
	SEARCH_RECALL_DEGRADE_LOG = "深分页超出召回上限，退化为窗口内重排: page=%d, size=%d, recallLimit=%d"
	// 检索统计回填失败后指标降级的日志消息
	SEARCH_STATS_FILL_DEGRADE_LOG = "文章统计回填失败，对应指标降级为 ES 文档原值: metrics=%s, error=%v"
	// 可选依赖缺失导致服务降级的警告
	DEPENDENCY_MANIFEST_DEGRADED = "可选依赖缺失，服务降级运行: %s"
	// 必需依赖缺失拒绝启动的错误消息
	DEPENDENCY_MANIFEST_REQUIRED_MISSING = "必需依赖缺失，拒绝启动，请检查配置后重试: %s"

	// ===== 用户日志 =====

	// 记录操作耗时的日志消息
	RECORD_DURATION_MESSAGE = "%s %s 使用了%dms"
	// 带用户身份的操作日志消息
	USER_LOG_MESSAGE = "用户%d:%s %s %s: %s"
	// 未登录用户的操作日志消息
	ANONYMOUS_USER_LOG_MESSAGE = "匿名用户 %s %s: %s"

	// ===== 搜索校验字段名 =====

	// 搜索开始时间字段的中文名
	SEARCH_START_TIME_FIELD = "开始时间"
	// 搜索结束时间字段的中文名
	SEARCH_END_TIME_FIELD = "结束时间"

	// ===== API日志 =====

	// 序列化 API 日志失败的错误消息
	SERIALIZE_API_LOG_FAIL_MESSAGE = "序列化 API 日志消息失败: %v"
	// API 日志投递失败的错误消息
	SEND_API_LOG_FAIL_MESSAGE = "发送 API 日志到队列失败: %v"
	// API 日志投递成功的日志消息
	SEND_API_LOG_SUCCESS_MESSAGE = "API 日志已发送到队列"
	// API 日志中用户 ID 的字段名
	API_LOG_USER_ID_FIELD = "用户ID"
	// API 日志中用户名的字段名
	API_LOG_USERNAME_FIELD = "用户名"
	// API 日志中会话 ID 的字段名
	API_LOG_SESSION_ID_FIELD = "会话ID"
	// API 日志中请求方法的字段名
	API_LOG_REQUEST_METHOD_FIELD = "请求方法"
	// API 日志中请求路径的字段名
	API_LOG_REQUEST_PATH_FIELD = "请求路径"
	// API 日志中接口描述的字段名
	API_LOG_DESCRIPTION_FIELD = "描述"
	// API 日志中查询参数的字段名
	API_LOG_QUERY_PARAMS_FIELD = "查询参数"
	// API 日志中请求体的字段名
	API_LOG_REQUEST_BODY_FIELD = "请求体"
	// API 日志查询参数的输出前缀
	API_LOG_QUERY_PARAMS_PREFIX = "查询参数: "
	// API 日志请求体的输出前缀
	API_LOG_REQUEST_BODY_PREFIX = "请求体: "
	// 日志内容被截断时追加的后缀
	LOG_TRUNCATED_SUFFIX = "...[截断]"
	// WebSocket 连接场景的日志描述
	API_LOG_WEBSOCKET_CONNECTION = "WebSocket连接"
	// SSE 连接场景的日志描述
	API_LOG_SSE_CONNECTION = "SSE连接"

	// ===== ES同步 =====

	// ES 客户端未初始化导致跳过同步的日志消息
	ES_CLIENT_NOT_INITIALIZED_MESSAGE = "ES 客户端未初始化，跳过 ES 同步"
	// ES 批量同步失败的日志消息
	ES_BULK_SYNC_ERROR_MESSAGE = "ES批量同步错误"
	// ES 同步存在失败项的日志消息
	ES_SYNC_HAS_FAILURES_MESSAGE = "ES同步有失败项"
	// ES 同步失败详情的日志消息
	ES_SYNC_FAILURE_DETAILS_MESSAGE = "ES同步失败: %+v"
	// ES 单批同步完成的日志消息
	ES_SYNC_BATCH_COMPLETED_MESSAGE = "第 %d 批同步完成，新增 %d 条，更新 %d 条"
	// ES 增量同步完成的日志消息
	ES_INCREMENTAL_SYNC_COMPLETED_MESSAGE = "ES 增量同步完成，新增 %d 条，更新 %d 条，删除 %d 条"
	// ES 精确同步开始的日志消息
	ES_EXACT_SYNC_STARTED_MESSAGE = "ES 精确同步开始，变更类型 %s，主键 %v"
	// ES 精确同步完成的日志消息
	ES_EXACT_SYNC_COMPLETED_MESSAGE = "ES 精确同步完成，变更类型 %s，处理 %d 条"
	// 定时任务开始同步 ES 的日志消息
	TASK_SYNC_ES_STARTED_MESSAGE = "[定时任务] 开始同步文章到 ElasticSearch"
	// 定时任务同步 ES 成功的日志消息
	TASK_SYNC_ES_COMPLETED_MESSAGE = "[定时任务] 同步成功"
	// 定时任务同步 ES 失败的日志消息
	TASK_SYNC_ES_FAILED_MESSAGE = "[定时任务] 同步文章到 ElasticSearch 失败：%v"
	// 定时任务注册失败的日志消息
	TASK_REGISTER_FAILED_MESSAGE = "[定时任务] 注册任务 %s 失败：%v"
	// 定时任务调度器启动的日志消息
	TASK_SCHEDULER_STARTED_MESSAGE = "[定时任务] 已启动"
	// 定时任务开关关闭的日志消息
	TASK_SCHEDULER_DISABLED_MESSAGE = "[定时任务] 定时任务开关已关闭，不注册本地调度任务"
	// 没有已发布文章可同步的日志消息
	NO_PUBLISHED_ARTICLES_TO_SYNC_MESSAGE = "没有已发布的文章可同步"
	// ES 索引存在性判断失败的日志消息
	INDEX_CHECK_ERROR_MESSAGE = "索引判断错误"
	// ES 索引创建失败的日志消息
	INDEX_CREATION_ERROR_MESSAGE = "索引创建错误"

	// ===== ES 查询 DSL 日志 =====

	// 输出 ES 查询 DSL 的调试日志
	ES_SEARCH_DSL_LOG = "ES 查询 DSL: index=%s, body=%s"
	// 构建 ES 查询 DSL 失败的日志消息
	ES_DSL_BUILD_FAIL = "构建 ES 查询 DSL 失败: %v"

	// ===== 内部令牌日志 =====

	// 内部服务鉴权缺少令牌请求头的日志消息
	INTERNAL_TOKEN_HEADER_MISSING_LOG = "[内部令牌验证] 缺少 %s 请求头，路径: %s"
	// 内部服务令牌校验失败的日志消息
	INTERNAL_TOKEN_VALIDATE_FAIL_LOG = "[内部令牌验证] 令牌验证失败: %v, 路径: %s"
	// 内部服务令牌过期的日志消息
	INTERNAL_TOKEN_EXPIRED_LOG = "[内部令牌验证] 令牌已过期，路径: %s"
	// 内部服务令牌服务名不匹配的日志消息
	INTERNAL_TOKEN_SERVICE_MISMATCH_LOG = "[内部令牌验证] 服务名不匹配，期望: %s, 实际: %s, 路径: %s"
	// 内部服务令牌校验成功的日志消息
	INTERNAL_TOKEN_VALIDATE_SUCCESS_LOG = "[内部令牌验证] 验证成功，用户ID: %d, 服务: %s, 路径: %s"

	// ===== 异常/错误消息 =====

	// 业务异常统一输出格式
	BUSINESS_ERROR_MESSAGE = "业务异常错误: %s\n错误详情: %s\n%s"
	// 异常恢复后输出堆栈的格式
	STACK_ERROR_MESSAGE = "堆栈错误信息: %v\n%s"
	// 异步任务 panic 被恢复的日志消息
	SAFE_GO_PANIC_RECOVERED_MESSAGE = "异步任务 %s 执行时发生 panic，已自动恢复: %v\n堆栈信息:\n%s"
	// 未预期异常的兜底响应文案
	UNIFIED_ERROR_RESPONSE_MESSAGE = "GoZero服务器错误"
	// 获取搜索历史失败的日志消息
	SEARCH_HISTORY_FAIL = "获取搜索历史失败"
	// 搜索历史解析失败的日志消息
	SEARCH_HISTORY_PARSE_FAIL = "搜索历史解析失败，降级为空列表: %v"
	// 缺少用户 ID 的错误消息
	USER_ID_LESS = "缺少用户ID"

	// ===== 远程调用响应解析错误 =====

	// 下游响应数据为空的错误消息
	RESPONSE_DATA_EMPTY = "响应数据为空"
	// 序列化响应数据失败的错误消息
	RESPONSE_DATA_SERIALIZE = "序列化响应数据失败: %w"
	// 反序列化响应数据失败的错误消息
	RESPONSE_DATA_DESERIALIZE = "反序列化响应数据失败: %w"
	// 响应 items 字段缺失或格式错误的错误消息
	RESPONSE_ITEMS_INVALID = "响应 items 字段缺失或格式不符"
	// 响应 items 元素格式错误的错误消息
	RESPONSE_ITEM_INVALID = "响应 items 元素格式不符"
	// 响应 items 元素缺少有效 article_id 的错误消息
	RESPONSE_ARTICLE_ID_INVALID = "响应 items 元素缺少有效的 article_id"
	// 响应 keywords 字段缺失或格式错误的错误消息
	RESPONSE_KEYWORDS_INVALID = "响应 keywords 字段缺失或格式不符"
	// 响应 keywords 元素格式错误的错误消息
	RESPONSE_KEYWORD_INVALID = "响应 keywords 元素格式不符"
	// 批量查询用户失败的日志消息
	BATCH_QUERY_USER_FAIL = "批量查询用户失败: %v"
	// 批量查询子分类失败的日志消息
	BATCH_QUERY_SUBCATEGORY_FAIL = "批量查询子分类失败: %v"

	// Redis 分布式锁
	// 获取分布式锁异常的错误消息
	REDIS_LOCK_ACQUIRE_ERROR = "获取分布式锁错误: %v"
	// 获取分布式锁失败并跳过执行的日志消息
	REDIS_LOCK_ACQUIRE_FAIL = "[分布式锁] 获取锁失败，跳过本次执行，key: %s"
	// 获取分布式锁成功的日志消息
	REDIS_LOCK_ACQUIRE_SUCCESS = "[分布式锁] 获取锁成功，key: %s"
	// 释放分布式锁异常的错误消息
	REDIS_LOCK_RELEASE_ERROR = "释放分布式锁错误: %v"
	// 释放分布式锁失败的日志消息
	REDIS_LOCK_RELEASE_FAIL = "[分布式锁] 释放锁失败，key: %s"
	// 释放分布式锁成功的日志消息
	REDIS_LOCK_RELEASE_SUCCESS = "[分布式锁] 释放锁成功，key: %s"

	// Redis 实时消息
	// 订阅 Redis 实时消息失败的错误消息
	REDIS_REALTIME_SUBSCRIBE_ERROR = "订阅 Redis 实时消息失败: %v"
	// 发布 Redis 实时消息失败的错误消息
	REDIS_REALTIME_PUBLISH_ERROR = "发布 Redis 实时消息失败: %v"
	// 处理 Redis 实时消息失败的错误消息
	REDIS_REALTIME_MESSAGE_ERROR = "处理 Redis 实时消息失败: %v"
	// Redis 实时消息总线未初始化的错误消息
	REDIS_REALTIME_BUS_NOT_INITIALIZED_ERROR = "Redis 实时消息总线未初始化"
	// Redis 实时消息格式无效的错误消息
	REDIS_REALTIME_INVALID_MESSAGE_FORMAT_ERROR = "处理 Redis 实时消息失败: 消息格式无效"
	// 批量标记消息已读失败的日志消息
	MARK_MESSAGE_READ_ERROR = "标记聊天消息已读失败: %v"

	// API日志操作描述（ApplyApiLog 的接口描述参数）
	// 测试 GoZero 服务接口的日志描述
	API_LOG_TEST_GOZERO_SERVICE = "测试GoZero服务"
	// 手动同步 ES 任务的日志描述
	API_LOG_MANUAL_SYNC_ES_TASK = "手动触发同步ES任务"
	// 获取搜索历史接口的日志描述
	API_LOG_GET_SEARCH_HISTORY = "获取搜索历史"
	// 搜索文章接口的日志描述
	API_LOG_SEARCH_ARTICLES = "搜索文章"
	// 获取未读消息数接口的日志描述
	API_LOG_GET_UNREAD_MESSAGE_COUNT = "获取未读消息数"
	// 获取全部未读消息数接口的日志描述
	API_LOG_GET_ALL_UNREAD_COUNTS = "获取所有未读消息数"
	// 获取队列状态接口的日志描述
	API_LOG_GET_QUEUE_STATUS = "获取队列状态"
	// 离开队列接口的日志描述
	API_LOG_LEAVE_QUEUE = "离开队列"
	// 获取聊天历史接口的日志描述
	API_LOG_GET_CHAT_HISTORY = "获取聊天历史"
	// 发送消息接口的日志描述
	API_LOG_SEND_MESSAGE = "发送消息"
	// 加入队列接口的日志描述
	API_LOG_JOIN_QUEUE = "加入队列"
	// 获取 SQL 工具表结构接口的日志描述
	API_LOG_SQL_TOOLS_GET_TABLES = "获取SQL工具表结构信息"
	// 执行 SQL 工具只读查询接口的日志描述
	API_LOG_SQL_TOOLS_EXECUTE_QUERY = "执行SQL工具只读查询"
	// API_LOG_PENDING_DESCRIPTION 是 handler.tpl 的占位描述，生成后必须替换为具体文案
	// 待补充接口描述时的占位文案
	API_LOG_PENDING_DESCRIPTION = "待补充接口描述"

	// Swagger
	// 获取 Swagger 页面失败的日志消息
	SWAGGER_PAGE_FETCH_FAIL = "获取 Swagger 页面失败"

	// FastAPI 客户端错误描述
	// FastAPI 返回的文章 ID 列表为空的错误消息
	FASTAPI_ARTICLE_IDS_EMPTY = "文章ID列表为空"
	// 文章 ID 列表与关键词同时为空的错误消息
	FASTAPI_ARTICLE_IDS_OR_KEYWORD_EMPTY = "文章ID列表为空或关键词为空"
	// 响应 weights 字段缺失或格式错误的错误消息
	FASTAPI_WEIGHTS_INVALID = "响应 weights 字段缺失或格式不符"
	// 响应权重键未识别的错误消息
	FASTAPI_WEIGHTS_UNKNOWN_KEY = "FastAPI 返回未知的权重键: %s"
	// 响应 es_script 字段缺失或格式错误的错误消息
	FASTAPI_SCRIPT_INVALID = "响应 es_script 字段缺失或格式不符"
	// 响应 script_params 字段缺失或格式错误的错误消息
	FASTAPI_SCRIPT_PARAMS_INVALID = "响应 script_params 字段缺失或格式不符"

	// 异步任务描述（SafeGo）
	// 同步 ES 异步任务的名称
	SAFE_GO_SYNC_ES_DATA = "同步ES数据"

	// ===== SQL 工具安全约束消息 =====

	// SQL 查询语句为空的提示
	SQL_TOOLS_QUERY_EMPTY = "SQL查询语句不能为空"
	// 命中非只读语句的提示
	SQL_TOOLS_FORBIDDEN_STATEMENT = "安全限制：只允许执行只读查询（SELECT/WITH/SHOW/DESC/DESCRIBE/EXPLAIN）"
	// 禁止执行多条 SQL 的提示
	SQL_TOOLS_MULTIPLE_STATEMENTS = "安全限制：禁止执行多条SQL语句"
	// 要求必须带 LIMIT 的提示
	SQL_TOOLS_LIMIT_REQUIRED = "安全限制：SQL查询必须包含LIMIT子句"
	// LIMIT 超过上限的提示
	SQL_TOOLS_LIMIT_EXCEEDED = "安全限制：LIMIT超过最大限制100"
	// 表名不在白名单的提示
	SQL_TOOLS_TABLE_NOT_ALLOWED = "安全限制：表 '%s' 不在白名单内"
	// SQL 语句长度超限的提示
	SQL_TOOLS_QUERY_TOO_LONG = "SQL查询语句长度不能超过%d个字符"
	// 表名长度超限的提示
	SQL_TOOLS_TABLE_NAME_TOO_LONG = "表名长度不能超过%d个字符"
	// SQL 查询执行失败的提示
	SQL_TOOLS_QUERY_FAILED = "执行SQL查询失败"
	// MySQL 连接未初始化的提示
	SQL_TOOLS_MYSQL_UNINITIALIZED = "MySQL 连接未初始化"
	// SQL 工具使用的 MySQL 驱动名
	SQL_TOOLS_MYSQL_DRIVER = "mysql"
)
