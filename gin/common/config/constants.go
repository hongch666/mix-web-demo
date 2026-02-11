package config

const (
	// 读取配置文件失败消息
	READ_CONFIG_FILE_ERROR_MESSAGE = "读取配置文件失败"

	// 解析配置文件失败消息
	PARSE_CONFIG_FILE_ERROR_MESSAGE = "解析配置文件失败"

	// 配置映射失败消息
	CONFIG_MAPPING_ERROR_MESSAGE = "配置映射失败"

	// ES连接使用用户名认证消息
	ES_CONNECTION_WITH_AUTH_MESSAGE = "ES连接使用用户名认证: %s"

	// ES连接成功消息
	ES_CONNECTION_SUCCESS_MESSAGE = "ES连接成功: %s"

	// ES连接失败消息
	ES_CONNECTION_FAILURE_MESSAGE = "ES连接失败: %v"

	// 数据库连接失败消息
	DATABASE_CONNECTION_FAILURE_MESSAGE = "数据库连接失败: %v"

	// 数据库获取实例失败消息
	DATABASE_GET_INSTANCE_FAILURE_MESSAGE = "获取数据库实例失败: %v"

	// 数据库连接成功消息
	DATABASE_CONNECTION_SUCCESS_MESSAGE = "数据库连接成功"

	// 数据库跳过迁移消息
	DATABASE_MIGRATE_SKIPPED_MESSAGE = "DB 为 nil，跳过表迁移/创建"

	// 表已存在消息
	TABLE_ALREADY_EXISTS_MESSAGE = "chat_messages 表已存在"

	// 创建表失败消息
	CREATE_TABLE_FAILURE_MESSAGE = "创建 chat_messages 表失败: %v"

	// 表创建成功消息
	CREATE_TABLE_SUCCESS_MESSAGE = "chat_messages 表不存在，已创建"

	// MongoDB连接认证消息
	MONGODB_CONNECTION_WITH_AUTH_MESSAGE = "MongoDB 连接使用认证: %s:%s@%s:%s"

	// MongoDB连接无认证消息
	MONGODB_CONNECTION_NO_AUTH_MESSAGE = "MongoDB 连接 (无认证): %s:%s"

	// MongoDB连接成功消息
	MONGODB_CONNECTION_SUCCESS_MESSAGE = "MongoDB 连接成功"

	// MongoDB连接失败消息
	MONGODB_CONNECTION_FAILURE_MESSAGE = "MongoDB 连接失败"

	// MongoDB Ping失败消息
	MONGODB_PING_FAILURE_MESSAGE = "MongoDB Ping 失败"

	// RabbitMQ连接失败消息
	RABBITMQ_CONNECTION_FAILURE_MESSAGE = "RabbitMQ 连接失败: %v"

	// RabbitMQ创建Channel失败消息
	RABBITMQ_CREATE_CHANNEL_FAILURE_MESSAGE = "创建 RabbitMQ Channel 失败: %v"

	// RabbitMQ初始化成功消息
	RABBITMQ_INITIALIZATION_SUCCESS_MESSAGE = "RabbitMQ 初始化成功"

	// 发送消息到队列失败消息
	SEND_MESSAGE_TO_QUEUE_FAILURE_MESSAGE = "发送消息到队列 [%s] 失败: %v"

	// 发送消息到队列成功消息
	SEND_MESSAGE_TO_QUEUE_SUCCESS_MESSAGE = "已发送到队列 [%s]: %s"

	// 关闭RabbitMQ连接消息
	CLOSE_RABBITMQ_CONNECTION_MESSAGE = "RabbitMQ 连接已关闭"

	// 创建缓存目录失败消息
	CREATE_CACHE_DIR_FAILURE_MESSAGE = "创建缓存目录失败: %v"

	// 创建日志目录失败消息
	CREATE_LOG_DIR_FAILURE_MESSAGE = "创建日志目录失败: %v"

	// 创建Nacos NamingClient失败消息
	CREATE_NACOS_NAMING_CLIENT_FAILURE_MESSAGE = "创建 Nacos NamingClient 失败: %v"

	// 服务注册失败消息
	SERVICE_REGISTRATION_FAILURE_MESSAGE = "服务注册失败: %v"

	// 服务注册成功消息
	SERVICE_REGISTRATION_SUCCESS_MESSAGE = "服务注册成功"

	// 定义队列失败消息
	DEFINE_QUEUE_FAILURE_MESSAGE = "定义队列 %s 失败: %w"

	// 定义队列成功消息
	DEFINE_QUEUE_SUCCESS_MESSAGE = "队列 %s 定义成功"

	// 创建表SQL语句
	CREATE_TABLE_SQL = `
		CREATE TABLE IF NOT EXISTS chat_messages (
			id bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '消息ID，主键',
			sender_id varchar(50) NOT NULL COMMENT '发送者用户ID',
			receiver_id varchar(50) NOT NULL COMMENT '接收者用户ID',
			content text NOT NULL COMMENT '消息内容',
			created_at datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
			PRIMARY KEY (id),
			KEY idx_chat_messages_sender_id (sender_id) COMMENT '发送者ID索引',
			KEY idx_chat_messages_receiver_id (receiver_id) COMMENT '接收者ID索引',
			KEY idx_chat_messages_created_at (created_at) COMMENT '创建时间索引',
			KEY idx_chat_messages_sender_receiver (
				sender_id,
				receiver_id,
				created_at
			) COMMENT '发送者接收者组合索引，用于查询聊天历史'
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天消息表';
	`

	// 初始相关消息

	// 初始欢迎消息
	WELCOME_MESSAGE = "Gin应用已启动"

	// 初始服务地址消息
	SERVICE_ADDRESS_MESSAGE = "服务地址: http://%s:%d"

	// 初始Swagger地址消息
	SWAGGER_ADDRESS_MESSAGE = "Swagger文档地址: http://%s:%d/swagger/index.html"
)
