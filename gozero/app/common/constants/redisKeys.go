package constants

// 集中定义项目内所有 Redis key / 前缀 / 模式，作为唯一来源。
//
// gozero 当前仅用 Redis 承载定时任务的分布式锁，所有锁 key 统一收口于此，
// 便于与兄弟服务（spring / gateway）的 key 约定保持一致、避免散落硬编码。
const (
	// Redis 分布式锁
	LOCK_TASK_ES_SYNC              = "lock:task:es:sync"
	LOCK_TASK_ES_SYNC_EXPIRE int64 = 3600
)
