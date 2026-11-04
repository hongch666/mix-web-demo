package svc

import (
	"app/common/cache"
	"app/common/constants"
	"app/common/redis"
	"app/common/utils"
	"app/internal/config"
	"app/internal/types"
	"app/model/chatMessages"
	"app/model/search"
)

// 创建 ModelContext 实例，初始化各业务模型依赖
func newModelContext(c config.Config, infrastructure *InfrastructureContext, clientCtx *ClientContext, logger *utils.ZeroLogger) *ModelContext {
	models := &ModelContext{}
	if infrastructure.MySQLConn != nil {
		models.ChatMessagesModel = chatMessages.NewChatMessagesModel(infrastructure.MySQLConn)
	}

	models.SearchModel = search.NewSearchModel(search.SearchModelDeps{
		ESClient:      infrastructure.ESClient,
		SpringClient:  clientCtx.SpringClient,
		DSLLogEnabled: c.Database.ES.DSLLogEnabled,
		Logger:        logger,
	})

	// 搜索结果缓存依赖 Redis：未装配 Redis 时保持 nil，搜索链路按未命中处理直接回源
	if infrastructure.RedisClient != nil {
		models.SearchResultCache = cache.NewMultiLevelCache[*types.SearchArticlesResp](cache.Options{
			KeyPrefix: constants.SEARCH_RESULT_CACHE_PREFIX,
			LocalTTL:  constants.SEARCH_RESULT_CACHE_LOCAL_TTL,
			RedisTTL:  constants.SEARCH_RESULT_CACHE_REDIS_TTL,
			Store:     redis.NewCacheStore(infrastructure.RedisClient),
			Logger:    logger,
		})
	}
	return models
}
