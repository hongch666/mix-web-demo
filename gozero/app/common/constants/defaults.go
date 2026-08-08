package constants

import "time"

// 配置默认值类 — 锁过期时间等
const (
	// 向量增强控制
	SEARCH_VECTOR_TIMEOUT_MS      = 1000
	SEARCH_VECTOR_CANDIDATE_LIMIT = 50

	// 图谱增强控制
	SEARCH_GRAPH_TIMEOUT_MS      = 800
	SEARCH_GRAPH_CANDIDATE_LIMIT = 50
)

// WebSocket 相关默认值
const (
	// WebSocket 读缓冲区大小（字节）
	WebSocketReadLimit = 512
	// WebSocket 发送通道缓冲区大小
	WebSocketSendBufferSize = 256
)

// SSE 相关默认值
const (
	// SSE 发送通道缓冲区大小
	SSESendBufferSize = 256
	// SSE 心跳间隔
	SSEHeartbeatInterval = 30 * time.Second
)

// Elasticsearch 相关默认值
const (
	// ES 最大重试次数
	ESMaxRetries = 3
	// ES 健康检查间隔
	ESHealthcheckInterval = 10 * time.Second
	// ES 启动超时
	ESHealthcheckTimeoutStartup = 5 * time.Second
)

// RabbitMQ / 消息队列相关默认值
const (
	// ES 同步批次间延迟
	ESSyncBatchDelay = 200 * time.Millisecond
)

// Nacos 相关默认值
const (
	// Nacos 客户端超时（毫秒）
	NacosClientTimeoutMs = 5000
)

// 数据库连接超时
const (
	// MongoDB 连接超时
	MongoDBConnectTimeout = 10 * time.Second
	// Redis 连接超时
	RedisConnectTimeout = 5 * time.Second
	// ServiceContext 关闭时 MongoDB 断开超时
	MongoDBDisconnectTimeout = 5 * time.Second
	// DDL 执行超时（如建表）
	DDLOperationTimeout = 10 * time.Second
)
