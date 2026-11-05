package constants

import "time"

// ===== 日期时间格式常量 =====

const (
	// DateTimeFormat 用于日志输出、ES 索引、API 响应等场景的标准日期时间格式
	DateTimeFormat = "2006-01-02 15:04:05"
	// EmptyTraceID 用于无活动链路上下文的日志
	EmptyTraceID = "-"
	// TraceLogFormat 统一文件日志中的 Trace ID 字段格式
	TraceLogFormat = "%s - %s - trace_id=%s - %s\n"
	// TraceLogFormatNoTime 不写时间戳的文件日志格式，用于容器部署（时间由 Loki 采集侧提供）
	TraceLogFormatNoTime = "%s - trace_id=%s - %s\n"
)

// ===== 配置默认值类 — 锁过期时间等 =====

const (
	// 搜索增强控制，召回放大档位：浅页按该粒度向上取整召回，使同一档位内各页共享同一候选集，归一化分母因此保持一致，跨页 FinalScore 可比较
	SEARCH_RECALL_STEP_SIZE = 100
	// 召回放大上限：page*size 超出该值时退化为窗口内重排，避免深分页拖垮 ES 与增强服务
	SEARCH_RECALL_MAX_SIZE = 200
	// 向量增强候选上限，需不小于召回放大上限，否则未参与增强的候选会缺失语义分
	SEARCH_VECTOR_CANDIDATE_LIMIT = 200
	// 图谱增强候选上限，需不小于召回放大上限
	SEARCH_GRAPH_CANDIDATE_LIMIT = 200
	// 单次搜索允许并入的图谱扩召回文章条数上限，需与 FastAPI 侧 GRAPH_RECALL_LIMIT 对齐
	SEARCH_GRAPH_RECALL_MAX = 10
	// 搜索结果 L1 本地缓存有效期，覆盖连续点击与快速翻页的相同查询
	SEARCH_RESULT_CACHE_LOCAL_TTL = 10 * time.Second
	// 搜索结果 L2 Redis 缓存有效期，供多实例复用，过期后重新检索
	SEARCH_RESULT_CACHE_REDIS_TTL = 30 * time.Second
	// 允许写入搜索结果缓存的单页条数上限，响应体过大的深分页不进入缓存
	SEARCH_RESULT_CACHE_MAX_SIZE = 20
	// 搜索算法配置 L1 本地缓存有效期，脚本、权重与参数名映射变更频率低，按此周期回源刷新
	SEARCH_CONFIG_CACHE_LOCAL_TTL = 5 * time.Minute
	// 搜索算法配置 L2 Redis 缓存有效期，供多实例复用并减少跨实例回源
	SEARCH_CONFIG_CACHE_REDIS_TTL = 24 * time.Hour
)

// 搜索统计回填指标，顺序与检索时并行拉取的顺序一一对应，作为 SEARCH_STATS_FILL_DEGRADE_LOG 的 metrics 字段使用，新增回填指标时同步追加，模型层按下标与回填结果对应
var SEARCH_STATS_FILL_METRICS = []string{
	"views", "likes", "collects", "author_follows", "comment_scores",
}

// ===== 多级缓存默认值 =====

const (
	// L1 本地缓存默认有效期，多级缓存未显式配置时使用，跨实例的本地值最多滞后该时长
	CACHE_LOCAL_TTL = time.Minute
	// L2 Redis 缓存默认有效期，多级缓存未显式配置时使用，取比 L1 更长的有效期以减少跨实例回源
	CACHE_REDIS_TTL = 5 * time.Minute
	// L1 本地缓存默认最大条目数，超出后淘汰最早写入的条目
	CACHE_LOCAL_MAX_ENTRIES = 128
)

// ===== WebSocket 相关默认值 =====

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

// ===== SSE 相关默认值 =====

const (
	// SSE 发送通道缓冲区大小
	SSESendBufferSize = 256
	// SSE 心跳间隔
	SSEHeartbeatInterval = 30 * time.Second
)

// ===== Elasticsearch 相关默认值 =====

const (
	// ES 最大重试次数
	ESMaxRetries = 3
	// ES 健康检查间隔
	ESHealthcheckInterval = 10 * time.Second
	// ES 启动超时
	ESHealthcheckTimeoutStartup = 5 * time.Second
)

// ===== RabbitMQ / 消息队列相关默认值 =====

const (
	// ES 同步批次间延迟
	ESSyncBatchDelay = 200 * time.Millisecond
)

// ===== Nacos 相关默认值 =====

const (
	// Nacos 客户端超时（毫秒）
	NacosClientTimeoutMs = 5000
	// Nacos 实例注册最大尝试次数
	NacosRegisterRetries = 5
	// Nacos 实例后台补注册最大尝试次数
	NacosRegisterBackgroundRetries = 15
	// Nacos 实例注册重试间隔
	NacosRegisterRetryInterval = 2 * time.Second
	// Nacos 后台补注册任务名，用于异常日志标识
	NacosRegisterTaskName = "nacos-register"
	// Nacos SDK 缓存目录名
	NacosCacheDirName = "cache"
	// Nacos SDK 日志目录名
	NacosLogDirName = "log"
	// Nacos SDK 目录不可写时的临时目录名
	NacosTempDirName = "nacos"
)

// ===== 数据库连接超时 =====

const (
	// Redis 连接超时
	RedisConnectTimeout = 5 * time.Second
	// DDL 执行超时（如建表）
	DDLOperationTimeout = 10 * time.Second
)

// 敏感字段掩码
const SENSITIVE_FIELD_MASK = "******"
