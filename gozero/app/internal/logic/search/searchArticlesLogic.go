// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package search

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"app/common/exceptions"
	"app/common/keys"
	"app/common/utils"
	"app/internal/client"
	"app/internal/svc"
	"app/internal/types"
	"app/model/search"

	amqp "github.com/rabbitmq/amqp091-go"
)

type SearchArticlesLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// 搜索文章
func NewSearchArticlesLogic(ctx context.Context, svcCtx *svc.ServiceContext) *SearchArticlesLogic {
	return &SearchArticlesLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
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

	// 执行ES搜索
	articles, total, err := l.svcCtx.SearchModel.SearchArticle(l.ctx, searchDTO)
	if err != nil {
		l.Error(fmt.Sprintf(utils.SEARCH_EXECUTION_ERROR+": %v", err))
		panic(exceptions.NewInternalServerError(utils.SEARCH_EXECUTION_ERROR, err.Error()))
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
			EsScore:           article.ESScore,
		}
	}

	l.Info(utils.ARTICLE_SEARCH_SUCCESS)

	resp = &types.SearchArticlesResp{
		Total: total,
		List:  items,
	}

	// 判断是否需要图谱增强
	mode := types.NormalizeSearchMode(req)
	graphEnabled := l.svcCtx.Config.Search.GraphEnabled

	if mode != "keyword" && graphEnabled && len(items) > 0 {
		resp.List = l.enhanceWithGraph(items, keyword, categoryName, subCategoryName, currentUserID, mode)
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

// enhanceWithGraph 调用图谱增强并融合重排
func (l *SearchArticlesLogic) enhanceWithGraph(
	items []types.ArticleEsItem,
	keyword string,
	categoryName string,
	subCategoryName string,
	userID int64,
	mode string,
) []types.ArticleEsItem {
	// 提取文章ID列表
	articleIDs := make([]int64, 0, len(items))
	for _, item := range items {
		articleIDs = append(articleIDs, item.Id)
	}

	// 从 tags 字符串提取标签
	tagList := extractTagsFromItems(items)

	// 构建图谱增强请求
	graphReq := &client.GraphEnhanceRequest{
		UserID:          userID,
		Keyword:         keyword,
		ArticleIDs:      articleIDs,
		CategoryName:    categoryName,
		SubCategoryName: subCategoryName,
		Tags:            tagList,
		Limit:           len(articleIDs),
		Mode:            mode,
	}

	// 调用图谱增强
	graphResp, err := l.svcCtx.GraphSearchClient.Enhance(l.ctx, graphReq)
	if err != nil {
		l.Warningf(utils.GRAPH_ENHANCE_DEGRADE_LOG,
			keyword, userID, len(articleIDs), err)

		if !l.svcCtx.Config.Search.GraphFallbackEnabled {
			return items
		}
		// 降级时清除图谱相关字段
		return items
	}

	// 融合重排
	hasKeyword := keyword != ""
	isLoggedIn := userID > 0

	fusionCfg := FusionConfig{
		GraphScoreWeight:  l.svcCtx.Config.Search.GraphScoreWeight,
		HybridMinESWeight: l.svcCtx.Config.Search.HybridMinESWeight,
		IsLoggedIn:        isLoggedIn,
		HasKeyword:        hasKeyword,
	}

	return MergeAndRerank(items, graphResp.Items, fusionCfg)
}

// extractTagsFromItems 从文章列表中提取所有标签
func extractTagsFromItems(items []types.ArticleEsItem) []string {
	tagSet := make(map[string]struct{})
	for _, item := range items {
		if item.Tags == "" {
			continue
		}
		for _, tag := range strings.Split(item.Tags, ",") {
			tag = strings.TrimSpace(tag)
			if tag != "" {
				tagSet[tag] = struct{}{}
			}
		}
	}

	tags := make([]string, 0, len(tagSet))
	for tag := range tagSet {
		tags = append(tags, tag)
	}
	return tags
}

func getCurrentUserFromContext(ctx context.Context) (int64, string) {
	userID, _ := ctx.Value(keys.UserIDKey).(int64)
	username, _ := ctx.Value(keys.UsernameKey).(string)
	return userID, username
}
