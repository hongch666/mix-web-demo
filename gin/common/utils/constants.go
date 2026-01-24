package utils

const (
	// Gin 自己的测试欢迎信息
	TEST_MESSAGE = "Hello,I am Gin!"

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

	// 搜索结果解析错误信息
	SEARCH_RESULT_PARSE_ERROR = "搜索结果解析错误"

	// 搜索指标信息
	SEARCH_METRICS_INFO = "[搜索评分] 文章ID:%d | 标题:%.30s | AI评分:%.2f | 用户评分:%.2f | 阅读量:%d | 点赞:%d | 收藏:%d | 作者关注:%d | 综合分数:%.4f"

	// 文章查询错误
	ARTICLE_QUERY_ERROR = "文章查询错误"

	// 子分类查询错误
	SUBCATEGORY_QUERY_ERROR = "子分类查询错误"

	// 分类查询错误
	CATEGORY_QUERY_ERROR = "分类查询错误"

	// 收藏查询错误
	COLLECT_QUERY_ERROR = "收藏查询错误"

	// 评分查询初始消息
	RATING_QUERY_START = "开始从MySQL查询 %d 篇文章的评分信息"

	// 评分查询MySQL错误消息
	RATING_QUERY_MYSQL_ERROR = "评分查询失败"

	// 评分查询完成消息
	RATING_QUERY_COMPLETED = "评分查询查询完成，共获取 %d 条评分记录"

	// 评分查询结果调试信息
	RATING_QUERY_RESULT_DEBUG = "[评分查询] 文章ID:%d | 类型:%s | 平均评分:%.2f | 评论数:%d"

	// 关注查询错误信息
	FOCUS_QUERY_ERROR = "关注查询错误"

	// 点赞查询错误信息
	LIKE_QUERY_ERROR = "点赞查询错误"

	// 用户查询错误信息
	USER_QUERY_ERROR = "用户查询错误"

	// 获取工作目录失败信息
	GET_WORKING_DIR_ERROR = "获取当前工作目录失败"

	// 创建日志目录失败信息
	CREATE_LOG_DIR_ERROR = "创建日志目录失败"

	// 打开日志文件失败信息
	OPEN_LOG_FILE_ERROR = "打开日志文件失败"

	// 写入日志文件失败信息
	WRITE_LOG_FILE_ERROR = "写入日志文件失败"

	// JSON序列化错误信息
	JSON_SERIALIZATION_ERROR = "JSON序列化失败"

	// 异常状态码信息
	UNEXPECTED_STATUS_CODE = "异常状态码: %d, 响应内容: %s"

	// 服务发现失败信息
	SERVICE_DISCOVERY_ERROR = "服务发现失败"

	// 无可用服务实例信息
	NO_AVAILABLE_SERVICE_INSTANCE = "无可用服务实例"

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

	// 业务异常错误消息
	BUSINESS_ERROR_MESSAGE = "业务异常错误: %s\n错误详情: %s\n%s"

	// 堆栈错误信息消息
	STACK_ERROR_MESSAGE = "堆栈错误信息: %v\n%s"

	// 统一错误响应消息
	UNIFIED_ERROR_RESPONSE_MESSAGE = "Gin服务器错误"

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
	TASK_SYNC_ES_STARTED_MESSAGE = "[定时任务] 开始同步文章到 Elasticsearch"

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

	// 搜索历史获取失败消息
	SEARCH_HISTORY_FAIL = "获取搜索历史失败"

	// 缺少用户ID消息
	USER_ID_LESS = "缺少用户ID"

	// WebSocket 连接失败消息
	WS_CONNECT_FAIL = "WebSocket连接失败"

	// SSE心跳写入失败
	SSE_HEARTBEAT_WRITE_FAIL = "SSE心跳写入失败: "

	// 跳过空的SSE消息
	EMPTY_SSE = "跳过空的SSE消息"

	// SSE写入失败
	SSE_WRITE_FAIL = "SSE写入失败: "

	// WebSocket 用户连接状态相关

	// 用户已连接
	USER_CONNECTED = "joined"

	// 用户已经在队列中
	USER_ALREADY_IN_QUEUE = "already_in_queue"

	// 用户已断开连接
	USER_DISCONNECTED = "left"

	// 用户不在队列中
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

	// 复杂语句

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
)
