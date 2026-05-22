// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package search

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"app/common/exceptions"
	"app/common/keys"
	"app/common/utils"
	"app/internal/client/fastapiClient"
	"app/internal/svc"
	"app/internal/types"
	"app/model/search"

	rabbitmq "github.com/wagslane/go-rabbitmq"
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

	mode := types.NormalizeSearchMode(req)
	vectorEnabled := types.IsVectorEnhanceEnabled(req, keyword, l.svcCtx.Config.Search.VectorEnabled)
	graphEnabled := types.IsGraphEnhanceEnabled(req, l.svcCtx.Config.Search.GraphEnabled)

	if len(items) > 0 {
		articleIDs := extractArticleIDsFromItems(items)
		tagList := extractTagsFromItems(items)
		vectorItems := make([]fastapiClient.VectorEnhanceItem, 0)
		graphItems := make([]fastapiClient.GraphEnhanceItem, 0)

		if vectorEnabled {
			vectorItems = l.fetchVectorEnhance(articleIDs, tagList, keyword, categoryName, subCategoryName, currentUserID, mode)
		}

		if graphEnabled {
			graphItems = l.fetchGraphEnhance(articleIDs, tagList, keyword, categoryName, subCategoryName, currentUserID, mode)
		}

		if vectorEnabled || graphEnabled {
			resp.List = MergeAndRerank(items, vectorItems, graphItems, FusionConfig{
				VectorScoreWeight: l.svcCtx.Config.Search.VectorScoreWeight,
				GraphScoreWeight:  l.svcCtx.Config.Search.GraphScoreWeight,
				HybridMinESWeight: l.svcCtx.Config.Search.HybridMinESWeight,
				IsLoggedIn:        currentUserID > 0,
				HasKeyword:        keyword != "",
				VectorEnabled:     len(vectorItems) > 0,
				GraphEnabled:      len(graphItems) > 0,
			})
		} else {
			FillDefaultScores(resp.List)
		}
	}

	if !types.IsExplainEnabled(req) {
		clearExplainFields(resp.List)
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
			"userId":  logUserID,
			"content": searchDTO,
			"msg":     utils.SEARCH_MSG,
		}
		jsonBytes, err := json.Marshal(msg)
		if err != nil {
			l.Error(fmt.Sprintf(utils.SEARCH_ERR+": %v", err))
		} else {
			// 通过RabbitMQ发送消息
			if l.svcCtx.RabbitMQPublisher != nil {
				err = l.svcCtx.RabbitMQPublisher.Publish(
					jsonBytes,
					[]string{"article-log-queue"},
					rabbitmq.WithPublishOptionsContentType("application/json"),
				)
				if err != nil {
					l.Error(fmt.Sprintf(utils.SEARCH_ERR+": %v", err))
				}
			}
		}
	}

	return
}

// fetchVectorEnhance 调用向量增强
func (l *SearchArticlesLogic) fetchVectorEnhance(
	articleIDs []int64,
	tagList []string,
	keyword string,
	categoryName string,
	subCategoryName string,
	userID int64,
	mode string,
) []fastapiClient.VectorEnhanceItem {
	limitedIDs := limitArticleIDs(articleIDs, l.svcCtx.Config.Search.VectorCandidateLimit)
	if len(limitedIDs) == 0 || keyword == "" {
		return []fastapiClient.VectorEnhanceItem{}
	}

	vectorReq := &fastapiClient.VectorEnhanceRequest{
		UserID:          userID,
		Keyword:         keyword,
		ArticleIDs:      limitedIDs,
		CategoryName:    categoryName,
		SubCategoryName: subCategoryName,
		Tags:            tagList,
		Limit:           len(limitedIDs),
		TopK:            len(limitedIDs),
		Mode:            mode,
	}

	ctx := l.ctx
	if l.svcCtx.Config.Search.VectorTimeoutMs > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(l.ctx, time.Duration(l.svcCtx.Config.Search.VectorTimeoutMs)*time.Millisecond)
		defer cancel()
	}

	result, err := l.svcCtx.FastapiClient.EnhanceVector(ctx, vectorReq)
	if err != nil {
		l.Warningf(utils.VECTOR_ENHANCE_DEGRADE_LOG,
			keyword, userID, len(limitedIDs), err)
		return []fastapiClient.VectorEnhanceItem{}
	}

	items, err := fastapiClient.ParseVectorEnhanceResult(result.Data)
	if err != nil {
		l.Warningf(utils.VECTOR_ENHANCE_DEGRADE_LOG,
			keyword, userID, len(limitedIDs), err)
		return []fastapiClient.VectorEnhanceItem{}
	}
	return items
}

// fetchGraphEnhance 调用图谱增强
func (l *SearchArticlesLogic) fetchGraphEnhance(
	articleIDs []int64,
	tagList []string,
	keyword string,
	categoryName string,
	subCategoryName string,
	userID int64,
	mode string,
) []fastapiClient.GraphEnhanceItem {
	limitedIDs := limitArticleIDs(articleIDs, l.svcCtx.Config.Search.GraphCandidateLimit)
	if len(limitedIDs) == 0 {
		return []fastapiClient.GraphEnhanceItem{}
	}

	graphReq := &fastapiClient.GraphEnhanceRequest{
		UserID:          userID,
		Keyword:         keyword,
		ArticleIDs:      limitedIDs,
		CategoryName:    categoryName,
		SubCategoryName: subCategoryName,
		Tags:            tagList,
		Limit:           len(limitedIDs),
		Mode:            mode,
	}

	ctx := l.ctx
	if l.svcCtx.Config.Search.GraphTimeoutMs > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(l.ctx, time.Duration(l.svcCtx.Config.Search.GraphTimeoutMs)*time.Millisecond)
		defer cancel()
	}

	graphResult, err := l.svcCtx.FastapiClient.EnhanceGraph(ctx, graphReq)
	if err != nil {
		l.Warningf(utils.GRAPH_ENHANCE_DEGRADE_LOG,
			keyword, userID, len(limitedIDs), err)
		return []fastapiClient.GraphEnhanceItem{}
	}

	items, err := fastapiClient.ParseGraphEnhanceResult(graphResult.Data)
	if err != nil {
		l.Warningf(utils.GRAPH_ENHANCE_DEGRADE_LOG,
			keyword, userID, len(limitedIDs), err)
		return []fastapiClient.GraphEnhanceItem{}
	}
	return items
}

// extractArticleIDsFromItems 从文章列表中提取文章ID
func extractArticleIDsFromItems(items []types.ArticleEsItem) []int64 {
	articleIDs := make([]int64, 0, len(items))
	for _, item := range items {
		articleIDs = append(articleIDs, item.Id)
	}
	return articleIDs
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

func limitArticleIDs(articleIDs []int64, limit int) []int64 {
	if limit <= 0 || limit > len(articleIDs) {
		limit = len(articleIDs)
	}
	return articleIDs[:limit]
}

func clearExplainFields(items []types.ArticleEsItem) {
	for i := range items {
		items[i].Reason = ""
		items[i].SemanticReason = ""
		items[i].Relations = make([]types.GraphRelation, 0)
		items[i].MatchedChunks = make([]types.VectorMatchedChunk, 0)
	}
}

func getCurrentUserFromContext(ctx context.Context) (int64, string) {
	userID, _ := ctx.Value(keys.UserIDKey).(int64)
	username, _ := ctx.Value(keys.UsernameKey).(string)
	return userID, username
}
