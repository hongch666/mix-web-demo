package constants

const (
	// 实时聊天消息发布频道
	REALTIME_CHAT_CHANNEL = "realtime:chat"

	// Redis 分布式锁
	LOCK_TASK_ES_SYNC              = "lock:task:es:sync"
	LOCK_TASK_ES_SYNC_EXPIRE int64 = 3600
)
