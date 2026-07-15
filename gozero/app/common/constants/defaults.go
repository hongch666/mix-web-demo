package constants

// 配置默认值类 — ES权重名称、锁过期时间等
const (
	// ES 搜索权重名称
	ES_WEIGHT_NAME            = "esWeight"
	AI_RATING_WEIGHT_NAME     = "aiWeight"
	USER_RATING_WEIGHT_NAME   = "userWeight"
	VIEWS_WEIGHT_NAME         = "viewsWeight"
	LIKES_WEIGHT_NAME         = "likesWeight"
	COLLECTS_WEIGHT_NAME      = "collectsWeight"
	AUTHOR_FOLLOW_WEIGHT_NAME = "followWeight"
	RECENCY_WEIGHT_NAME       = "recencyWeight"

	// 归一化参数名称
	RECENCY_DECAY_DAYS_NAME     = "decayDaysSq"
	MAX_VIEWS_NORMALIZED_NAME   = "maxViewsNormalized"
	MAX_LIKES_NORMALIZED_NAME   = "maxLikesNormalized"
	MAX_COLLECTS_NORMALIZED_NAME = "maxCollectsNormalized"
	MAX_FOLLOWS_NORMALIZED_NAME = "maxFollowsNormalized"

	// Redis 分布式锁
	LOCK_TASK_ES_SYNC        = "lock:task:es:sync"
	LOCK_TASK_ES_SYNC_EXPIRE int64 = 3600
)
