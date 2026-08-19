package svc

import (
	"app/internal/config"
	"app/model/aiHistory"
	"app/model/chatMessages"
	"app/model/search"
)

// 创建 ModelContext 实例，初始化各业务模型依赖
func newModelContext(_ config.Config, infrastructure *InfrastructureContext, clientCtx *ClientContext) *ModelContext {
	models := &ModelContext{}
	if infrastructure.MySQLConn != nil {
		models.AiHistoryModel = aiHistory.NewAiHistoryModel(infrastructure.MySQLConn)
		models.ChatMessagesModel = chatMessages.NewChatMessagesModel(infrastructure.MySQLConn)
	}

	models.SearchModel = search.NewSearchModel(search.SearchModelDeps{
		ESClient:     infrastructure.ESClient,
		SpringClient: clientCtx.SpringClient,
	})
	return models
}
