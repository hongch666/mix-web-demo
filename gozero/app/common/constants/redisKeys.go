package constants

const (
	// ===== 实时广播频道 =====

	// 实时聊天消息发布频道
	REALTIME_CHAT_CHANNEL = "realtime:chat"

	// ===== Redis 分布式锁 =====

	// ES 同步任务的分布式锁 key
	LOCK_TASK_ES_SYNC = "lock:task:es:sync"
	// ES 同步锁的过期秒数
	LOCK_TASK_ES_SYNC_EXPIRE int64 = 3600
)
