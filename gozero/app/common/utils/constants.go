package utils

const (
	// GoZero 自己的测试欢迎信息
	TEST_MESSAGE = "Hello,I am GoZero!"

	// dev 模式下 Nacos 注册消息
	REGISTER_NACOS_DEV_MODE_MESSAGE = "SERVER_MODE=dev，Nacos 注册统一使用 127.0.0.1"

	// 文章搜索错误信息
	SEARCH_ERR = "文章搜索错误"

	// 文字搜索消息
	SEARCH_MSG = "发起了文章搜索"

	// 解析错误信息
	PARSE_ERR = "解析错误"

	// WebSocket 消息发送成功信息
	WS_SEND_SUCCESS = "消息 %d 通过WebSocket发送成功，已标记为已读"

	// WebSocket 消息发送失败信息
	WS_SEND_FAIL = "用户 %s 不在线，消息 %d 已保存为未读"

	// 标记已读失败信息
	MARK_READ_FAIL = "标记消息 %d 为已读失败"

	// 用户加入聊天队列信息
	USER_JOINED_QUEUE = "用户 %s 已加入聊天队列"

	// 用户离开聊天队列信息
	USER_LEFT_QUEUE = "用户 %s 已离开聊天队列"

	// 用户在队列但未连接信息
	USER_IN_QUEUE_NOT_CONNECTED = "用户 %s 在队列中但没有WebSocket连接，无法发送实时消息"

	// WebSocket 错误信息
	WS_ERROR = "WebSocket 错误: %v"

	// 解析消息失败信息
	PARSE_MESSAGE_FAIL = "解析消息失败: %v"

	// SSE 注册成功信息
	SSE_REGISTER_SUCCESS = "SSE客户端 %s 已注册"

	// SSE 注销成功信息
	SSE_UNREGISTER_SUCCESS = "SSE客户端 %s 已注销"

	// 发送空消息警告信息
	SSE_SEND_EMPTY_WARNING = "尝试发送空通知给用户 %s"

	// 用户 SSE 客户端未找到警告信息
	SSE_CLIENT_NOT_FOUND_WARNING = "用户 %s 的SSE客户端未找到"

	// SSE 消息发送成功信息
	SSE_SEND_SUCCESS = "SSE通知已发送给用户 %s"

	// SSE 消息发送失败警告信息
	SSE_SEND_FAIL_WARNING = "无法发送SSE通知给用户 %s,通道已满"

	// SSE 广播消息发送成功信息
	SSE_BROADCAST_SUCCESS = "广播消息已发送给用户 %s"

	// SSE 广播消息发送失败警告信息
	SSE_BROADCAST_FAIL_WARNING = "无法广播消息给用户 %s，通道已满"

	// 发送空的SSE消息警告信息
	SSE_SEND_EMPTY_MESSAGE_WARNING = "尝试发送空的SSE消息"

	// 序列化SSE消息错误信息
	SSE_SERIALIZE_MESSAGE_ERROR = "序列化SSE消息错误: %v"

	// 序列化 SSE 消息为空消息
	SSE_SERIALIZE_MESSAGE_EMPTY = "序列化后的SSE消息为null"

	// 消息创建错误信息
	CREATE_MESSAGE_ERROR = "消息创建错误"

	// 获取历史消息错误信息
	GET_HISTORY_MESSAGE_ERROR = "获取消息历史错误"

	// 获取两个用户间未读消息数错误信息
	GET_UNREAD_COUNT_ERROR = "获取两个用户间未读消息数错误"

	// 获取用户与其他所有人的未读消息数错误信息
	GET_ALL_UNREAD_COUNTS_ERROR = "获取用户与其他所有人的未读消息数错误"

	// 搜索执行错误信息
	SEARCH_EXECUTION_ERROR = "搜索执行错误"

	// 文章查询错误
	ARTICLE_QUERY_ERROR = "文章查询错误"

	// 分类查询错误
	CATEGORY_QUERY_ERROR = "分类查询错误"

	// 收藏查询错误
	COLLECT_QUERY_ERROR = "收藏查询错误"

	// 关注查询错误信息
	FOCUS_QUERY_ERROR = "关注查询错误"

	// 点赞查询错误信息
	LIKE_QUERY_ERROR = "点赞查询错误"

	// 获取工作目录失败信息
	GET_WORKING_DIR_ERROR = "获取当前工作目录失败"

	// 未找到本机可用的IPv4地址信息
	LOCAL_IPV4_ADDRESS_NOT_FOUND_ERROR = "未找到本机可用的 IPv4 地址"

	// 创建日志目录失败信息
	CREATE_LOG_DIR_ERROR = "创建日志目录失败"

	// 初始化日志失败信息
	ZERO_LOGGER_INIT_FAIL = "初始化日志失败: %v"

	// 初始化 Gorm 失败信息
	GORM_INIT_FAIL = "初始化 Gorm 失败: %v"

	// 初始化 ES 客户端失败信息
	ES_CLIENT_INIT_FAIL = "初始化 ES 客户端失败: %v"

	// 初始化 RabbitMQ 连接失败信息
	RABBITMQ_CONNECTION_INIT_FAIL = "初始化 RabbitMQ 连接失败: %v"

	// 初始化 RabbitMQ 通道失败信息
	RABBITMQ_CHANNEL_INIT_FAIL = "初始化 RabbitMQ 通道失败: %v"

	// 声明 RabbitMQ 队列失败信息
	RABBITMQ_DECLARE_QUEUE_FAIL = "声明 RabbitMQ 队列失败, queue=%s, err=%v"

	// 初始化 MongoDB 连接失败信息
	MONGODB_CONNECTION_INIT_FAIL = "初始化 MongoDB 连接失败: %v"

	// MongoDB 心跳检测失败信息
	MONGODB_PING_FAIL = "MongoDB 心跳检测失败: %v"

	// 初始化 Nacos 客户端失败信息
	NACOS_CLIENT_INIT_FAIL = "初始化 Nacos 客户端失败: %v"

	// Nacos 注册失败信息
	NACOS_REGISTER_FAIL = "Nacos 注册失败: service=%s, address=%s:%d, group=%s, err=%v"

	// 打开日志文件失败信息
	OPEN_LOG_FILE_ERROR = "打开日志文件失败"

	// 写入日志文件失败信息
	WRITE_LOG_FILE_ERROR = "写入日志文件失败"

	// 获取工作目录失败错误消息 (用于 logger)
	LOGGER_GET_WORKDIR_ERROR = "获取工作目录失败: %w"

	// 创建日志目录失败错误消息 (用于 logger)
	LOGGER_CREATE_DIR_ERROR = "创建日志目录失败: %w"

	// 打开日志文件失败错误消息 (用于 logger)
	LOGGER_OPEN_FILE_ERROR = "打开日志文件失败: %v"

	// 写入日志文件失败错误消息 (用于 logger)
	LOGGER_WRITE_FILE_ERROR = "写入日志文件失败: %v"

	// 读取配置文件失败信息
	READ_CONFIG_FILE_ERROR = "读取配置文件失败: %s, %v"

	// 解析配置文件失败信息
	PARSE_CONFIG_FILE_ERROR = "解析配置文件失败: %s, %v"

	// 自动建表失败信息
	AUTO_CREATE_TABLE_FAIL = "自动创建 chat_messages 表失败: %v"

	// 自动建表成功信息
	AUTO_CREATE_TABLE_SUCCESS = "自动创建 chat_messages 表成功"

	// JSON序列化错误信息
	JSON_SERIALIZATION_ERROR = "JSON序列化失败"

	// 异常状态码信息
	UNEXPECTED_STATUS_CODE = "异常状态码: %d, 响应内容: %s"

	// 服务发现失败信息
	SERVICE_DISCOVERY_ERROR = "服务发现失败"

	// 无可用服务实例信息
	NO_AVAILABLE_SERVICE_INSTANCE = "无可用服务实例"

	// 服务调用失败信息
	SERVICE_CALL_FAILED = "服务调用失败: %s"

	// 记录耗时消息
	RECORD_DURATION_MESSAGE = "%s %s 使用了%dms"

	// 用户日志消息
	USER_LOG_MESSAGE = "用户%d:%s %s %s: %s"

	// 匿名用户日志消息
	ANONYMOUS_USER_LOG_MESSAGE = "匿名用户 %s %s: %s"

	// 序列化API日志失败消息
	SERIALIZE_API_LOG_FAIL_MESSAGE = "序列化 API 日志消息失败: %v"

	// 发送API日志到消息队列失败消息
	SEND_API_LOG_FAIL_MESSAGE = "发送 API 日志到队列失败: %v"

	// 发送API日志到消息队列成功消息
	SEND_API_LOG_SUCCESS_MESSAGE = "API 日志已发送到队列"

	// 发送API日志时RabbitMQ未初始化消息
	SEND_API_LOG_RABBITMQ_NOT_INITIALIZED_MESSAGE = "RabbitMQ 未初始化，无法发送 API 日志"

	// RabbitMQ 通道未初始化消息
	RABBITMQ_CHANNEL_NOT_INITIALIZED_MESSAGE = "RabbitMQ 通道未初始化"

	// ES 客户端未初始化消息
	ES_CLIENT_NOT_INITIALIZED_MESSAGE = "ES 客户端未初始化，跳过 ES 同步"

	// WebSocket 连接建立消息
	WEBSOCKET_CONNECTION_ESTABLISHED_MESSAGE = "WebSocket 连接已建立"

	// 内部令牌验证：缺少请求头
	INTERNAL_TOKEN_HEADER_MISSING_LOG = "[内部令牌验证] 缺少 %s 请求头，路径: %s"

	// 内部令牌验证：令牌为空
	INTERNAL_TOKEN_EMPTY_LOG = "[内部令牌验证] 令牌为空，路径: %s"

	// 内部令牌验证：验证失败
	INTERNAL_TOKEN_VALIDATE_FAIL_LOG = "[内部令牌验证] 令牌验证失败: %v, 路径: %s"

	// 内部令牌验证：令牌已过期
	INTERNAL_TOKEN_EXPIRED_LOG = "[内部令牌验证] 令牌已过期，路径: %s"

	// 内部令牌验证：服务名不匹配
	INTERNAL_TOKEN_SERVICE_MISMATCH_LOG = "[内部令牌验证] 服务名不匹配，期望: %s, 实际: %s, 路径: %s"

	// 内部令牌验证：验证成功
	INTERNAL_TOKEN_VALIDATE_SUCCESS_LOG = "[内部令牌验证] 验证成功，用户ID: %d, 服务: %s, 路径: %s"

	// SSE 连接建立消息
	SSE_CONNECTION_ESTABLISHED_MESSAGE = "SSE 连接已建立"

	// 获取未读消息数失败消息
	GET_UNREAD_COUNT_MESSAGE_ERROR = "获取未读消息数失败: %v"

	// 查询用户失败消息
	QUERY_USER_ERROR = "查询用户 %d 失败: %v"

	// 查询子分类失败消息
	QUERY_SUBCATEGORY_ERROR = "查询子分类 %d 失败: %v"

	// 查询分类失败消息
	QUERY_CATEGORY_ERROR = "查询分类 %d 失败: %v"

	// 业务异常错误消息
	BUSINESS_ERROR_MESSAGE = "业务异常错误: %s\n错误详情: %s\n%s"

	// 堆栈错误信息消息
	STACK_ERROR_MESSAGE = "堆栈错误信息: %v\n%s"

	// 子 goroutine panic 恢复日志
	SAFE_GO_PANIC_RECOVERED_MESSAGE = "异步任务 %s 执行时发生 panic，已自动恢复: %v\n堆栈信息:\n%s"

	// 统一错误响应消息
	UNIFIED_ERROR_RESPONSE_MESSAGE = "服务器错误"

	// 索引判断错误消息
	INDEX_CHECK_ERROR_MESSAGE = "索引判断错误"

	// 索引创建错误消息
	INDEX_CREATION_ERROR_MESSAGE = "索引创建错误"

	// 索引删除错误消息
	INDEX_DELETION_ERROR_MESSAGE = "索引删除错误"

	// 批量获取文章评分完成消息
	BULK_FETCH_ARTICLE_RATINGS_COMPLETED_MESSAGE = "批量获取 %d 篇文章的评分信息完成"

	// ES批量同步错误消息
	ES_BULK_SYNC_ERROR_MESSAGE = "ES批量同步错误"

	// ES同步有失败项消息
	ES_SYNC_HAS_FAILURES_MESSAGE = "ES同步有失败项"

	// ES同步失败详情消息
	ES_SYNC_FAILURE_DETAILS_MESSAGE = "ES同步失败: %+v"

	// ES同步批次提交完成消息
	ES_SYNC_BATCH_SUBMISSION_COMPLETED_MESSAGE = "第 %d/%d 批提交完成，共 %d 条记录"

	// 定时任务同步ES启动消息
	TASK_SYNC_ES_STARTED_MESSAGE = "[定时任务] 开始同步文章到 ElasticSearch"

	// 定时任务同步ES完成消息
	TASK_SYNC_ES_COMPLETED_MESSAGE = "[定时任务] 同步成功"

	// 定时任务同步ES失败消息
	TASK_SYNC_ES_FAILED_MESSAGE = "[定时任务] 注册同步任务失败：%v"

	// 定时任务已启动消息
	TASK_SCHEDULER_STARTED_MESSAGE = "[定时任务] 已启动"

	// 批量获取文章点赞和收藏完成消息
	BULK_FETCH_ARTICLE_LIKES_COLLECTS_COMPLETED_MESSAGE = "批量获取 %d 篇文章的点赞和收藏信息完成"

	// 批量获取作者关注信息完成消息
	BULK_FETCH_AUTHOR_FOLLOWS_COMPLETED_MESSAGE = "批量获取 %d 个作者的关注信息完成"

	// 无已发布文章可同步消息
	NO_PUBLISHED_ARTICLES_TO_SYNC_MESSAGE = "没有已发布的文章可同步"

	// 参数错误消息
	PARAM_ERR = "参数错误"

	// 用户ID格式错误
	USER_ID_ERR = "用户ID格式错误"

	// 通用字段为空错误格式
	FIELD_EMPTY_ERROR = "%s不能为空"

	// 通用字段必须是正整数错误格式
	FIELD_POSITIVE_INT_ERROR = "%s必须是正整数"

	// 通用字段必须大于0错误格式
	FIELD_GREATER_THAN_ZERO_ERROR = "%s必须大于0"

	// 发送者ID字段名
	CHAT_SENDER_ID_FIELD = "发送者ID"

	// 接收者ID字段名
	CHAT_RECEIVER_ID_FIELD = "接收者ID"

	// 用户ID字段名
	USER_ID_FIELD = "用户ID"

	// 对方用户ID字段名
	OTHER_USER_ID_FIELD = "对方用户ID"

	// 消息内容为空错误
	CHAT_CONTENT_EMPTY_ERROR = "消息内容不能为空"

	// 页码必须大于0错误
	SEARCH_PAGE_GREATER_THAN_ZERO_ERROR = "页码必须大于0"

	// 每页数量必须大于0错误
	SEARCH_SIZE_GREATER_THAN_ZERO_ERROR = "每页数量必须大于0"

	// 聊天历史页码必须大于0错误
	CHAT_HISTORY_PAGE_GREATER_THAN_ZERO_ERROR = "页码必须大于0"

	// 聊天历史每页数量必须大于0错误
	CHAT_HISTORY_SIZE_GREATER_THAN_ZERO_ERROR = "每页数量必须大于0"

	// 开始时间不能晚于结束时间错误
	SEARCH_START_AFTER_END_ERROR = "开始时间不能晚于结束时间"

	// 搜索时间格式错误模板
	SEARCH_TIME_FORMAT_ERROR = "%s格式必须为%s"

	// 搜索历史获取失败消息
	SEARCH_HISTORY_FAIL = "获取搜索历史失败"

	// 缺少用户ID消息
	USER_ID_LESS = "缺少用户ID"

	// 文章搜索成功消息（带详情）
	ARTICLE_SEARCH_SUCCESS = "文章搜索成功"

	// 聊天消息发送成功消息
	CHAT_MESSAGE_SEND_SUCCESS = "聊天消息发送成功"

	// 获取聊天历史成功消息
	GET_CHAT_HISTORY_SUCCESS = "获取聊天历史成功"

	// 获取未读消息数成功消息
	GET_UNREAD_COUNT_SUCCESS = "获取未读消息数成功"

	// 获取所有未读消息数成功消息
	GET_ALL_UNREAD_COUNTS_SUCCESS = "获取所有未读消息数成功"

	// 加入队列成功消息
	JOIN_QUEUE_SUCCESS = "加入聊天队列成功"

	// 离开队列成功消息
	LEAVE_QUEUE_SUCCESS = "离开聊天队列成功"

	// 获取队列状态成功消息
	GET_QUEUE_STATUS_SUCCESS = "获取队列状态成功"

	// WebSocket 连接失败消息
	WS_CONNECT_FAIL = "WebSocket连接失败"

	// SSE心跳写入失败
	SSE_HEARTBEAT_WRITE_FAIL = "SSE心跳写入失败: "

	// 跳过空的SSE消息
	EMPTY_SSE = "跳过空的SSE消息"

	// SSE写入失败消息
	SSE_WRITE_FAIL = "SSE写入失败: "

	// 配置信息描述
	CONFIG_DESCRIPTION = "配置文件路径，默认为 etc/application.yaml"

	// WebSocket 用户连接状态相关

	// 用户已连接消息
	USER_CONNECTED = "joined"

	// 用户已经在队列中消息
	USER_ALREADY_IN_QUEUE = "already_in_queue"

	// 用户已断开连接消息
	USER_DISCONNECTED = "left"

	// 用户不在队列中消息
	USER_NOT_IN_QUEUE = "not_in_queue"

	// 心跳检测消息
	HEARTBEAT_MESSAGE = "ping"

	// 心跳响应消息
	HEARTBEAT_RESPONSE = "pong"

	// SSE 心跳消息
	SSE_HEARTBEAT = ": heartbeat\n\n"

	// 搜索相关

	// ES 搜索算法脚本
	ES_SEARCH_SCRIPT = `
		double esScore = 1.0 / (1.0 + Math.exp(-_score));
		double score = params.esWeight * esScore;

		double aiBoost = params.aiWeight * (doc['ai_score'].size() > 0 ? doc['ai_score'].value / 10.0 : 0);

		double userBoost = params.userWeight * (doc['user_score'].size() > 0 ? doc['user_score'].value / 10.0 : 0);

		double viewsBoost = params.viewsWeight * Math.min((double)doc['views'].value / params.maxViewsNormalized, 1.0);

		double likesBoost = params.likesWeight * (doc['likeCount'].size() > 0 ? Math.min((double)doc['likeCount'].value / params.maxLikesNormalized, 1.0) : 0);

		double collectsBoost = params.collectsWeight * (doc['collectCount'].size() > 0 ? Math.min((double)doc['collectCount'].value / params.maxCollectsNormalized, 1.0) : 0);

		double followBoost = params.followWeight * (doc['authorFollowCount'].size() > 0 ? Math.min((double)doc['authorFollowCount'].value / params.maxFollowsNormalized, 1.0) : 0);

		long now = System.currentTimeMillis();
		long articleTime = doc['create_at'].value.getMillis();
		long daysDiff = (now - articleTime) / (1000L * 86400L);
		double recencyScore = Math.exp(-1.0 * (daysDiff * daysDiff) / (2.0 * params.decayDaysSq));
		double recencyBoost = params.recencyWeight * recencyScore;

		return score + aiBoost + userBoost + viewsBoost + likesBoost + collectsBoost + followBoost + recencyBoost;
	`

	// ES权重名称
	ES_WEIGHT_NAME = "esWeight"

	// AI评分权重名称
	AI_RATING_WEIGHT_NAME = "aiWeight"

	// 用户评分权重名称
	USER_RATING_WEIGHT_NAME = "userWeight"

	// 阅读量权重名称
	VIEWS_WEIGHT_NAME = "viewsWeight"

	// 点赞量权重名称
	LIKES_WEIGHT_NAME = "likesWeight"

	// 收藏量权重名称
	COLLECTS_WEIGHT_NAME = "collectsWeight"

	// 作者关注数权重名称
	AUTHOR_FOLLOW_WEIGHT_NAME = "followWeight"

	// 文章新鲜度权重名称
	RECENCY_WEIGHT_NAME = "recencyWeight"

	// 新鲜度衰减天数名称
	RECENCY_DECAY_DAYS_NAME = "decayDaysSq"

	// 最大阅读量归一化名称
	MAX_VIEWS_NORMALIZED_NAME = "maxViewsNormalized"

	// 最大点赞量归一化名称
	MAX_LIKES_NORMALIZED_NAME = "maxLikesNormalized"

	// 最大收藏量归一化名称
	MAX_COLLECTS_NORMALIZED_NAME = "maxCollectsNormalized"

	// 最大关注量归一化名称
	MAX_FOLLOWS_NORMALIZED_NAME = "maxFollowsNormalized"

	// 数据库 SQL 脚本

	// chat_messages 表创建 SQL 语句
	CREATE_CHAT_MESSAGES_TABLE_SQL = `
		CREATE TABLE IF NOT EXISTS chat_messages (
			id bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '消息ID，主键',
			sender_id varchar(50) NOT NULL COMMENT '发送者ID',
			receiver_id varchar(50) NOT NULL COMMENT '接收者ID',
			content text NOT NULL COMMENT '消息内容',
			is_read tinyint NOT NULL DEFAULT 0 COMMENT '是否已读，0未读，1已读',
			created_at datetime(3) DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
			PRIMARY KEY (id),
			KEY idx_sender_receiver (sender_id, receiver_id)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天消息表';
	`

	// 复杂查询语句

	// comments表联合users表查询评分信息
	COMMENT_RATING_QUERY = `
		SELECT
			c.article_id,
			CASE WHEN u.role = 'ai' THEN 'ai' ELSE 'user' END as role_type,
			AVG(c.star) as avg_star,
			COUNT(*) as comment_count
		FROM comments c
		LEFT JOIN user u ON c.user_id = u.id
		WHERE c.article_id IN (?) AND c.star > 0
		GROUP BY c.article_id, role_type
	`

	// ES 索引映射定义
	ES_INDEX_MAPPING = `{
		"mappings": {
			"properties": {
				"id": { "type": "integer" },
				"title": { "type": "text", "analyzer": "ik_smart", "search_analyzer": "ik_smart" },
				"content": { "type": "text", "analyzer": "ik_smart", "search_analyzer": "ik_smart" },
				"userId": { "type": "integer" },
				"username": { "type": "keyword" },
				"category_name": { "type": "keyword" },
				"sub_category_name": { "type": "keyword" },
				"tags": { "type": "text", "analyzer": "ik_smart", "search_analyzer": "ik_smart" },
				"status": { "type": "integer" },
				"views": { "type": "integer" },
				"likeCount": { "type": "integer" },
				"collectCount": { "type": "integer" },
				"authorFollowCount": { "type": "integer" },
				"create_at": { "type": "date", "format": "yyyy-MM-dd HH:mm:ss" },
				"update_at": { "type": "date", "format": "yyyy-MM-dd HH:mm:ss" },
				"ai_score": { "type": "float" },
				"user_score": { "type": "float" },
				"ai_comment_count": { "type": "integer" },
				"user_comment_count": { "type": "integer" }
			}
		}
	}`

	// 内部服务令牌相关常量

	// 内部令牌密钥不能为空错误消息
	INTERNAL_TOKEN_SECRET_NOT_NULL = "内部服务令牌密钥不能为空"

	// 缺少内部令牌请求头错误消息
	INTERNAL_TOKEN_MISSING = "缺少必需的内部服务令牌请求头"

	// 内部令牌验证失败错误消息
	INTERNAL_TOKEN_INVALID = "内部服务令牌无效"

	// 内部令牌过期错误消息
	INTERNAL_TOKEN_EXPIRED = "内部服务令牌已过期"

	// 服务名称不匹配错误消息
	SERVICE_NAME_MISMATCH = "服务名称不匹配"

	// 用户加入队列消息（不含参数）
	USER_JOINED_QUEUE_MESSAGE = "用户已加入聊天队列"

	// 用户离开队列消息（不含参数）
	USER_LEFT_QUEUE_MESSAGE = "用户已离开聊天队列"

	// 用户在队列但未连接警告（不含参数）
	USER_IN_QUEUE_NOT_CONNECTED_WARNING = "用户在队列中但没有WebSocket连接，无法发送实时消息"

	// SSE客户端注册成功消息（不含参数）
	SSE_REGISTER_SUCCESS_MESSAGE = "SSE客户端已注册"

	// SSE客户端注销成功消息（不含参数）
	SSE_UNREGISTER_SUCCESS_MESSAGE = "SSE客户端已注销"

	// SSE通知发送成功消息（不含参数）
	SSE_SEND_SUCCESS_MESSAGE = "SSE通知已发送"

	// SSE通知发送失败警告（不含参数）
	SSE_SEND_FAIL_WARNING_MESSAGE = "无法发送SSE通知，通道已满"

	// SSE客户端未找到警告（不含参数）
	SSE_CLIENT_NOT_FOUND_WARNING_MESSAGE = "SSE客户端未找到"

	// SSE广播消息发送成功消息（不含参数）
	SSE_BROADCAST_SUCCESS_MESSAGE = "广播消息已发送"

	// SSE广播消息发送失败警告（不含参数）
	SSE_BROADCAST_FAIL_WARNING_MESSAGE = "无法广播消息，通道已满"

	// SSE发送空通知警告（不含参数）
	SSE_SEND_EMPTY_WARNING_MESSAGE = "尝试发送空通知"

	// SSE发送空消息警告（不含参数）
	SSE_SEND_EMPTY_MESSAGE_WARNING_MESSAGE = "尝试发送空的SSE消息"

	// SSE消息序列化错误（不含参数）
	SSE_SERIALIZE_MESSAGE_ERROR_MESSAGE = "序列化SSE消息错误"

	// API日志发送失败消息
	API_LOG_SEND_FAIL_MESSAGE = "[API日志发送失败] 队列: api-log-queue, 错误: %v"

	// API日志发送成功消息
	API_LOG_SEND_SUCCESS_MESSAGE = "[API日志发送成功] 队列: api-log-queue, 消息: %s"

	// Swagger 文档相关常量

	// 服务启动消息
	SERVER_START_MESSAGE = "服务启动于 %s:%d..."

	// Swagger 文档地址消息
	SWAGGER_DOCS_MESSAGE = "Swagger 文档地址 http://%s:%d/swagger/index.html"

	// 服务初始IP
	INIT_IP = "127.0.0.1"

	// 服务启动成功消息
	SERVER_START_SUCCESS = "服务启动成功"

	// 获取Swagger失败消息
	GET_SWAGGER_FAIL = "获取 Swagger 文档失败"

	// Swagger 静态HTML
	SWAGGER_HTML = `<!DOCTYPE html>
		<html>
		<head>
			<title>GoZero API 文档</title>
			<meta charset="UTF-8">
			<meta name="viewport" content="width=device-width, initial-scale=1">
			<link rel="stylesheet" href="/swagger/swagger-ui.css">
		</head>
		<body>
			<div id="swagger-ui"></div>
			<script src="/swagger/swagger-ui-bundle.js"></script>
			<script src="/swagger/swagger-ui-standalone-preset.js"></script>
			<script>
				window.onload = function() {
					SwaggerUIBundle({
						url: '/swagger/doc.json',
						dom_id: '#swagger-ui',
						presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
						layout: 'StandaloneLayout',
						deepLinking: true
					})
				}
			</script>
		</body>
		</html>
	`
)
