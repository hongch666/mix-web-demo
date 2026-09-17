package constants

import "time"

// 日期时间格式常量
const (
	// DateTimeFormat 用于日志输出、ES 索引、API 响应等场景的标准日期时间格式
	DateTimeFormat = "2006-01-02 15:04:05"
)

// 配置默认值类 — 锁过期时间等
const (
	// 搜索增强控制
	// 召回放大档位：浅页按该粒度向上取整召回，使同一档位内各页共享同一候选集
	// 归一化分母因此保持一致，跨页 FinalScore 可比较
	SEARCH_RECALL_STEP_SIZE = 100
	// 召回放大上限：page*size 超出该值时退化为窗口内重排，避免深分页拖垮 ES 与增强服务
	SEARCH_RECALL_MAX_SIZE = 200
	// 向量增强候选上限，需不小于召回放大上限，否则未参与增强的候选会缺失语义分
	SEARCH_VECTOR_CANDIDATE_LIMIT = 200
	// 图谱增强候选上限，需不小于召回放大上限
	SEARCH_GRAPH_CANDIDATE_LIMIT = 200
)

// WebSocket 相关默认值
const (
	// WebSocket 读缓冲区大小（字节）
	WebSocketReadLimit = 512
	// WebSocket 发送通道缓冲区大小
	WebSocketSendBufferSize = 256
	// WebSocket 服务端主动 ping 间隔
	WebSocketPingInterval = 30 * time.Second
	// WebSocket 等待客户端 pong 的最大时长
	WebSocketPongWait = 60 * time.Second
	// WebSocket 单次写操作超时
	WebSocketWriteWait = 10 * time.Second
	// WebSocket 已读回执数据库操作超时
	WebSocketReadReceiptTimeout = 5 * time.Second
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
	// Redis 连接超时
	RedisConnectTimeout = 5 * time.Second
	// DDL 执行超时（如建表）
	DDLOperationTimeout = 10 * time.Second
)
