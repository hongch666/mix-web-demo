package svc

import (
	"app/internal/config"
	"app/model/aiHistory"
	"app/model/articles"
	"app/model/category"
	"app/model/categoryReference"
	"app/model/chatMessages"
	"app/model/collects"
	"app/model/comments"
	"app/model/focus"
	"app/model/likes"
	"app/model/search"
	"app/model/subCategory"
	"app/model/user"
)

// 创建 ModelContext 实例，初始化各业务模型依赖
func newModelContext(c config.Config, infrastructure *InfrastructureContext) *ModelContext {
	models := &ModelContext{}
	if infrastructure.MySQLConn != nil {
		models.AiHistoryModel = aiHistory.NewAiHistoryModel(infrastructure.MySQLConn)
		models.ArticlesModel = articles.NewArticlesModel(infrastructure.MySQLConn)
		models.CategoryModel = category.NewCategoryModel(infrastructure.MySQLConn)
		models.CategoryReferenceModel = categoryReference.NewCategoryReferenceModel(infrastructure.MySQLConn)
		models.ChatMessagesModel = chatMessages.NewChatMessagesModel(infrastructure.MySQLConn)
		models.CollectsModel = collects.NewCollectsModel(infrastructure.MySQLConn)
		models.CommentsModel = comments.NewCommentsModel(infrastructure.MySQLConn)
		models.FocusModel = focus.NewFocusModel(infrastructure.MySQLConn)
		models.LikesModel = likes.NewLikesModel(infrastructure.MySQLConn)
		models.SubCategoryModel = subCategory.NewSubCategoryModel(infrastructure.MySQLConn)
		models.UserModel = user.NewUserModel(infrastructure.MySQLConn)
	}

	models.SearchModel = search.NewSearchModel(search.SearchModelDeps{
		ESClient:      infrastructure.ESClient,
		MongoClient:   infrastructure.MongoClient,
		MongoDatabase: c.Database.MongoDB.Database,
		ArticlesModel: models.ArticlesModel,
		LikesModel:    models.LikesModel,
		CollectsModel: models.CollectsModel,
		FocusModel:    models.FocusModel,
	})
	return models
}
