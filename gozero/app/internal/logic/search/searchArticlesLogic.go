// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package search

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"app/common/constants"
	"app/common/exceptions"
	"app/common/keys"
	"app/common/utils"
	"app/internal/client/fastapiClient"
	"app/internal/svc"
	"app/internal/types"
	"app/model/search"

	rabbitmq "github.com/wagslane/go-rabbitmq"

	"github.com/zeromicro/go-zero/core/mr"
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

	// 并行从 FastAPI 拉取 ES 搜索脚本三件套：脚本模板、权重与参数名映射（各自缓存 60s）
	var script search.SearchScript
	var weights search.SearchWeights
	var paramMap search.ScriptParamMapping
	var scriptErr, weightsErr, paramErr error
	_ = mr.Finish(
		func() error {
			script, scriptErr = l.svcCtx.FastapiClient.GetSearchScript(l.ctx)
			return nil
		},
		func() error {
			weights, weightsErr = l.svcCtx.FastapiClient.GetSearchWeights(l.ctx)
			return nil
		},
		func() error {
			paramMap, paramErr = l.svcCtx.FastapiClient.GetSearchScriptParams(l.ctx)
			return nil
		},
	)

	// 脚本模板、权重与脚本参数名映射任一失败都降级为普通 ES 条件分页查询
	// 权重缺失后无法计算融合权重，故降级路径同时放弃召回放大与向量、图谱增强
	degraded := scriptErr != nil || weightsErr != nil || paramErr != nil
	if degraded {
		l.Warningf(constants.SEARCH_SCRIPTS_FETCH_DEGRADE_LOG, scriptErr, weightsErr, paramErr)
	}

	// 解析 ES 召回窗口：浅页放大召回后由业务层切页，深页维持窗口内重排
	// 降级路径不做融合重排，直接按请求页码与页大小查询
	queryPage, querySize := page, size
	amplified := false
	if !degraded {
		var recallSize int
		queryPage, recallSize, amplified = resolveRecallWindow(page, size)
		querySize = recallSize
		if !amplified {
			l.Warningf(constants.SEARCH_RECALL_DEGRADE_LOG, page, size, constants.SEARCH_RECALL_MAX_SIZE)
		}
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
		Page:            queryPage,
		Size:            querySize,
	}

	// 执行ES搜索：降级路径不传脚本模板与权重，由 es.go 走普通条件查询
	var esScript string
	var searchWeights *search.SearchWeights
	if !degraded {
		esScript = script.EsScript
		searchWeights = &weights
	}
	articles, total, err := l.svcCtx.SearchModel.SearchArticle(l.ctx, searchDTO, esScript, searchWeights, paramMap)
	if err != nil {
		l.Error(fmt.Sprintf(constants.SEARCH_EXECUTION_ERROR+": %v", err))
		return nil, exceptions.NewInternalServerError(constants.SEARCH_EXECUTION_ERROR, err.Error())
	}

	// 转换为ArticleEsItem，此时 items 是召回候选集，切出目标页在融合重排之后进行
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
			CreateAt:          derefString(article.CreateAt),
			UpdateAt:          derefString(article.UpdateAt),
			AiScore:           article.AIScore,
			UserScore:         article.UserScore,
			AiCommentCount:    article.AICommentCount,
			UserCommentCount:  article.UserCommentCount,
			EsScore:           article.ESScore,
		}
	}

	l.Info(constants.ARTICLE_SEARCH_SUCCESS)

	resp = &types.SearchArticlesResp{
		Total: total,
		List:  items,
	}

	if degraded {
		// 降级路径不启用向量与图谱增强，仅归一化 ES 分用于展示
		FillDefaultScores(resp.List)
	} else if len(items) > 0 {
		mode := normalizeSearchMode(req)
		vectorEnabled := isVectorEnhanceEnabled(req, keyword)
		graphEnabled := isGraphEnhanceEnabled(req)

		articleIDs := extractArticleIDsFromItems(items)
		tagList := extractTagsFromItems(items)
		vectorItems := make([]fastapiClient.VectorEnhanceItem, 0)
		graphItems := make([]fastapiClient.GraphEnhanceItem, 0)

		// 向量增强与图谱增强是两次相互独立的远程调用，用 mr.Finish 并发执行
		var enhanceTasks []func() error
		if vectorEnabled {
			enhanceTasks = append(enhanceTasks, func() error {
				vectorItems = l.fetchVectorEnhance(articleIDs, tagList, keyword, categoryName, subCategoryName, currentUserID, mode)
				return nil
			})
		}
		if graphEnabled {
			enhanceTasks = append(enhanceTasks, func() error {
				graphItems = l.fetchGraphEnhance(articleIDs, tagList, keyword, categoryName, subCategoryName, currentUserID, mode)
				return nil
			})
		}
		if len(enhanceTasks) > 0 {
			_ = mr.Finish(enhanceTasks...)
		}

		if vectorEnabled || graphEnabled {
			resp.List = MergeAndRerank(items, vectorItems, graphItems, FusionConfig{
				VectorScoreWeight: weights.VectorScoreWeight,
				GraphScoreWeight:  weights.GraphScoreWeight,
				HybridMinESWeight: weights.HybridMinESWeight,
				IsLoggedIn:        currentUserID > 0,
				HasKeyword:        keyword != "",
				VectorEnabled:     len(vectorItems) > 0,
				GraphEnabled:      len(graphItems) > 0,
			})
		} else {
			FillDefaultScores(resp.List)
		}
	}

	// 融合重排作用于召回候选集，此处按分页窗口切出目标页
	if amplified {
		resp.List = pageSlice(resp.List, page, size)
	}

	if !isExplainEnabled(req) {
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
			"msg":     constants.SEARCH_MSG,
		}
		jsonBytes, err := json.Marshal(msg)
		if err != nil {
			l.Error(fmt.Sprintf(constants.SEARCH_ERR+": %v", err))
		} else if l.svcCtx.RabbitMQPublisher != nil {
			// 通过RabbitMQ发送消息
			err = l.svcCtx.RabbitMQPublisher.Publish(
				jsonBytes,
				[]string{"article-log-queue"},
				rabbitmq.WithPublishOptionsContentType("application/json"),
			)
			if err != nil {
				l.Error(fmt.Sprintf(constants.SEARCH_ERR+": %v", err))
			}
		}
	}

	return
}

// derefString 将 *string 安全解引用为 string，nil 时返回空串
func derefString(s *string) string {
	if s == nil {
		return ""
	}
	return *s
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
	limitedIDs := limitArticleIDs(articleIDs, constants.SEARCH_VECTOR_CANDIDATE_LIMIT)
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

	result, err := l.svcCtx.FastapiClient.EnhanceVector(l.ctx, vectorReq)
	if err != nil {
		l.Warningf(constants.VECTOR_ENHANCE_DEGRADE_LOG,
			keyword, userID, len(limitedIDs), err)
		return []fastapiClient.VectorEnhanceItem{}
	}

	items, err := fastapiClient.ParseVectorEnhanceResult(result.Data)
	if err != nil {
		l.Warningf(constants.VECTOR_ENHANCE_DEGRADE_LOG,
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
	limitedIDs := limitArticleIDs(articleIDs, constants.SEARCH_GRAPH_CANDIDATE_LIMIT)
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

	graphResult, err := l.svcCtx.FastapiClient.EnhanceGraph(l.ctx, graphReq)
	if err != nil {
		l.Warningf(constants.GRAPH_ENHANCE_DEGRADE_LOG,
			keyword, userID, len(limitedIDs), err)
		return []fastapiClient.GraphEnhanceItem{}
	}

	items, err := fastapiClient.ParseGraphEnhanceResult(graphResult.Data)
	if err != nil {
		l.Warningf(constants.GRAPH_ENHANCE_DEGRADE_LOG,
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

// resolveRecallWindow 解析 ES 召回窗口
// 返回 ES 查询使用的页码、条数以及是否开启召回放大
// 放大开启时 ES 从第 1 页按档位取 recallSize 条，融合重排后由 pageSlice 切出目标页
// page*size 超出召回上限或档位取整结果无法覆盖目标页时退化为窗口内重排
func resolveRecallWindow(page int, size int) (queryPage int, recallSize int, amplified bool) {
	windowSize := page * size
	step := constants.SEARCH_RECALL_STEP_SIZE
	recallLimit := min(
		constants.SEARCH_RECALL_MAX_SIZE,
		constants.SEARCH_VECTOR_CANDIDATE_LIMIT,
		constants.SEARCH_GRAPH_CANDIDATE_LIMIT,
	)

	// 按档位向上取整，使同一档位内各页召回同一批候选，归一化分母因此保持一致
	recallSize = ((windowSize + step - 1) / step) * step
	if windowSize > recallLimit || recallSize > recallLimit || recallSize < windowSize {
		return page, size, false
	}

	return 1, recallSize, true
}

// pageSlice 从融合重排后的候选集中切出目标页
func pageSlice(items []types.ArticleEsItem, page int, size int) []types.ArticleEsItem {
	start := (page - 1) * size
	if start >= len(items) {
		return make([]types.ArticleEsItem, 0)
	}

	end := min(start+size, len(items))
	return items[start:end]
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
