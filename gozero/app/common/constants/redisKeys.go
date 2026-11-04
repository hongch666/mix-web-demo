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

	// ===== 搜索配置缓存 Key =====

	// 搜索排序权重在 Redis 中的缓存 key，由多级缓存组件按 prefix + 业务 key 组装
	SEARCH_CONFIG_WEIGHTS_CACHE_KEY = "cache:search:config:weights"
	// ES 搜索脚本模板在 Redis 中的缓存 key
	SEARCH_CONFIG_SCRIPT_CACHE_KEY = "cache:search:config:script"
	// 脚本参数名映射在 Redis 中的缓存 key
	SEARCH_CONFIG_SCRIPT_PARAMS_CACHE_KEY = "cache:search:config:script_params"

	// ===== 搜索结果缓存 Key =====

	// 搜索结果多级缓存的 key 前缀，运行时拼接用户与全部查询条件的稳定摘要
	SEARCH_RESULT_CACHE_PREFIX = "cache:search:result:"
)
