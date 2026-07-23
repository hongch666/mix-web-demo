package constants

// 配置默认值类 — 锁过期时间等
const (
	// 向量增强控制
	SEARCH_VECTOR_TIMEOUT_MS     = 1000
	SEARCH_VECTOR_CANDIDATE_LIMIT = 50

	// 图谱增强控制
	SEARCH_GRAPH_TIMEOUT_MS      = 800
	SEARCH_GRAPH_CANDIDATE_LIMIT = 50

	// Redis 分布式锁
	LOCK_TASK_ES_SYNC              = "lock:task:es:sync"
	LOCK_TASK_ES_SYNC_EXPIRE int64 = 3600
)
