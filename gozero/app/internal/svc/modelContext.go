package svc

import (
	"app/common/utils"
	"app/internal/config"
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
	return models
}
