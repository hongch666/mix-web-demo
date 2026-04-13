// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package search

import (
	"context"
	"encoding/json"
	"fmt"

	"app/common/exceptions"
	"app/common/keys"
	"app/common/logger"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
	"app/model/search"

	amqp "github.com/rabbitmq/amqp091-go"
)

type SearchArticlesLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*logger.ZeroLogger
}

// 搜索文章
func NewSearchArticlesLogic(ctx context.Context, svcCtx *svc.ServiceContext) *SearchArticlesLogic {
	return &SearchArticlesLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger,
	}
}

func (l *SearchArticlesLogic) SearchArticles(req *types.SearchArticlesReq) (resp *types.SearchArticlesResp, err error) {
	// 设置默认分页
	page := max(req.Page, 1)
	size := req.Size
	if size < 1 {
		size = 10
	}

	// 构建搜索DTO
	keyword := ""
	if req.Keyword != nil {
		keyword = *req.Keyword
	}
	username := ""
	if req.Username != nil {
		username = *req.Username
	}
	categoryName := ""
	if req.CategoryName != nil {
		categoryName = *req.CategoryName
	}
	subCategoryName := ""
	if req.SubCategoryName != nil {
		subCategoryName = *req.SubCategoryName
	}

	currentUserID, _ := getCurrentUserFromContext(l.ctx)
	userID := req.UserId

	searchDTO := search.ArticleSearchDTO{
		Keyword:         keyword,
		UserID:          userID,
		Username:        username,
		CategoryName:    categoryName,
		SubCategoryName: subCategoryName,
		StartDate:       req.StartDate,
		EndDate:         req.EndDate,
		Page:            page,
		Size:            size,
	}

	// 执行搜索
	articles, total, err := l.svcCtx.SearchModel.SearchArticle(l.ctx, searchDTO)
	if err != nil {
		l.Error(fmt.Sprintf(utils.SEARCH_EXECUTION_ERROR+": %v", err))
		panic(exceptions.NewBusinessError(utils.SEARCH_EXECUTION_ERROR, err.Error()))
	}

	// 转换为ArticleEsItem
	items := make([]types.ArticleEsItem, len(articles))
	for i, article := range articles {
		items[i] = types.ArticleEsItem{
			Id:                article.ID,
			Title:             article.Title,
			Content:           article.Content,
			UserId:            article.UserID,
			Username:          article.Username,
			Tags:              article.Tags,
			Status:            article.Status,
			Views:             article.Views,
			LikeCount:         article.LikeCount,
			CollectCount:      article.CollectCount,
			AuthorFollowCount: article.AuthorFollowCount,
			CategoryName:      article.CategoryName,
			SubCategoryName:   article.SubCategoryName,
			CreateAt:          article.CreateAt,
			UpdateAt:          article.UpdateAt,
			AiScore:           article.AIScore,
			UserScore:         article.UserScore,
			AiCommentCount:    article.AICommentCount,
			UserCommentCount:  article.UserCommentCount,
		}
	}

	l.Info(utils.ARTICLE_SEARCH_SUCCESS)

	resp = &types.SearchArticlesResp{
		Total: total,
		List:  items,
	}

	// 如果指定了搜索关键字，记录搜索信息
	if req.Keyword != nil && *req.Keyword != "" {
		logUserID := currentUserID
		if logUserID <= 0 && req.UserId != nil {
			logUserID = int64(*req.UserId)
		}

		// 发送搜索信息到消息队列中进行异步处理
		msg := map[string]any{
			"action":  "search",
			"user_id": logUserID,
			"content": searchDTO,
			"msg":     utils.SEARCH_MSG,
		}
		jsonBytes, err := json.Marshal(msg)
		if err != nil {
			l.Error(fmt.Sprintf(utils.SEARCH_ERR+": %v", err))
		} else {
			// 通过RabbitMQ发送消息
			if l.svcCtx.RabbitMQChannel != nil {
				err = l.svcCtx.RabbitMQChannel.Publish(
					"",                  // exchange
					"article-log-queue", // routing key
					false,               // mandatory
					false,               // immediate
					amqp.Publishing{
						ContentType: "application/json",
						Body:        jsonBytes,
					},
				)
				if err != nil {
					l.Error(fmt.Sprintf(utils.SEARCH_ERR+": %v", err))
				}
			}
		}
	}

	return
}

func getCurrentUserFromContext(ctx context.Context) (int64, string) {
	userID, _ := ctx.Value(keys.UserIDKey).(int64)
	username, _ := ctx.Value(keys.UsernameKey).(string)
	return userID, username
}
