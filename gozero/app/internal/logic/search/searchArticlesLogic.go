// Code scaffolded by goctl. Safe to edit.

package search

import (
	"context"
	"strconv"
	"strings"
	"time"

	"app/common/constants"
	"app/common/exceptions"
	"app/common/keys"
	"app/common/metrics"
	"app/common/utils"
	"app/internal/client/fastapiClient"
	"app/internal/svc"
	"app/internal/types"
	"app/model/search"

	"github.com/zeromicro/go-zero/core/mr"
)

// SearchArticlesLogic 处理搜索文章接口请求的逻辑对象
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

// SearchArticles 处理搜索文章接口请求，相同用户与相同查询条件在缓存 TTL 内直接复用检索结果，未命中时执行 ES 检索、向量与图谱增强融合重排，并记录搜索日志
func (l *SearchArticlesLogic) SearchArticles(req *types.SearchArticlesReq) (resp *types.SearchArticlesResp, err error) {
	startedAt := time.Now()
	mode := "hybrid"
	defer func() {
		result := "success"
		if err != nil {
			result = "failure"
		}
		metrics.SearchRequests.WithLabelValues(mode, result).Inc()
		metrics.SearchDuration.WithLabelValues(mode).Observe(time.Since(startedAt).Seconds())
	}()

	// 设置默认分页
	page, size := normalizePaging(req)
	currentUserID, _ := getCurrentUserFromContext(l.ctx)

	// 缓存回源函数：检索结果写入两级缓存，并把本次实际生效的模式回填给指标
	loader := func(ctx context.Context) (*types.SearchArticlesResp, error) {
		result, searchMode, searchErr := l.search(ctx, req, page, size)
		mode = searchMode
		return result, searchErr
	}

	// 深分页响应体过大，不进入结果缓存，直接回源
	cache := l.svcCtx.SearchResultCache
	if cache == nil || size > constants.SEARCH_RESULT_CACHE_MAX_SIZE {
		return loader(l.ctx)
	}

	resp, err = cache.Get(
		l.ctx,
		buildSearchResultCacheKey(req, page, size, currentUserID),
		loader,
	)
	if err != nil {
		return nil, err
	}

	// 搜索历史按请求记录，命中缓存时同样投递，避免行为日志缺失
	l.publishSearchLog(req, page, size, currentUserID)
	return resp, nil
}

// search 执行一次完整检索：拉取脚本三件套、ES 召回、向量与图谱增强、融合重排与切页，返回实际生效的搜索模式
func (l *SearchArticlesLogic) search(
	ctx context.Context,
	req *types.SearchArticlesReq,
	page int,
	size int,
) (*types.SearchArticlesResp, string, error) {
	mode := "hybrid"

	// 并行从 FastAPI 拉取 ES 搜索脚本三件套：脚本模板、权重与参数名映射（走本地加 Redis 两级缓存，回源失败降级本地旧值）
	var script search.SearchScript
	var weights search.SearchWeights
	var paramMap search.ScriptParamMapping
	var scriptErr, weightsErr, paramErr error
	_ = mr.Finish(
		func() error {
			script, scriptErr = l.svcCtx.FastapiClient.GetSearchScript(ctx)
			return nil
		},
		func() error {
			weights, weightsErr = l.svcCtx.FastapiClient.GetSearchWeights(ctx)
			return nil
		},
		func() error {
			paramMap, paramErr = l.svcCtx.FastapiClient.GetSearchScriptParams(ctx)
			return nil
		},
	)

	// 脚本模板、权重与脚本参数名映射任一失败都降级为普通 ES 条件分页查询，权重缺失后无法计算融合权重，故降级路径同时放弃召回放大与向量、图谱增强
	degraded := scriptErr != nil || weightsErr != nil || paramErr != nil
	if degraded {
		mode = "keyword"
		l.Warningf(constants.SEARCH_SCRIPTS_FETCH_DEGRADE_LOG, scriptErr, weightsErr, paramErr)
	}

	// 解析 ES 召回窗口：浅页放大召回后由业务层切页，深页维持窗口内重排，降级路径不做融合重排，直接按请求页码与页大小查询
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
	keyword := derefString(req.Keyword)
	username := derefString(req.Username)
	categoryName := derefString(req.CategoryName)
	subCategoryName := derefString(req.SubCategoryName)

	currentUserID, _ := getCurrentUserFromContext(ctx)
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
	articles, total, err := l.svcCtx.SearchModel.SearchArticle(ctx, searchDTO, esScript, searchWeights, paramMap)
	if err != nil {
		l.Errorf(constants.SEARCH_EXECUTION_ERROR+": %v", err)
		return nil, mode, exceptions.NewInternalServerError(constants.SEARCH_EXECUTION_ERROR, err.Error())
	}

	// 转换为ArticleEsItem，此时 items 是召回候选集，切出目标页在融合重排之后进行
	items := toArticleEsItems(articles)

	l.Info(constants.ARTICLE_SEARCH_SUCCESS)

	resp := &types.SearchArticlesResp{
		Total: total,
		List:  items,
	}

	// 降级路径不启用向量与图谱增强，仅归一化 ES 分用于展示
	if degraded {
		FillDefaultScores(resp.List)
		return resp, mode, nil
	}

	if len(items) > 0 {
		searchMode := normalizeSearchMode(req)
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
				vectorItems = l.fetchVectorEnhance(articleIDs, tagList, keyword, categoryName, subCategoryName, currentUserID, searchMode)
				return nil
			})
		}
		if graphEnabled {
			enhanceTasks = append(enhanceTasks, func() error {
				graphItems = l.fetchGraphEnhance(articleIDs, tagList, keyword, categoryName, subCategoryName, currentUserID, searchMode)
				return nil
			})
		}
		if len(enhanceTasks) > 0 {
			_ = mr.Finish(enhanceTasks...)
		}

		// 图谱扩召回会把候选集之外的关联文章带回，按 id 从 ES 补齐后才能参与融合与切页
		if graphEnabled && amplified {
			items = l.appendGraphRecallItems(items, graphItems)
			resp.List = items
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

	return resp, mode, nil
}

// normalizePaging 归一化分页参数，页码小于 1 取 1，页大小小于 1 取 10
func normalizePaging(req *types.SearchArticlesReq) (int, int) {
	page := max(req.Page, 1)
	size := req.Size
	if size < 1 {
		size = 10
	}
	return page, size
}

// buildSearchResultCacheKey 按用户与全部查询条件生成稳定缓存键，任一条件不同都不会命中同一缓存
func buildSearchResultCacheKey(req *types.SearchArticlesReq, page int, size int, currentUserID int64) string {
	authorID := ""
	if req.UserId != nil {
		authorID = strconv.FormatUint(*req.UserId, 10)
	}

	return utils.StableKey(
		strconv.FormatInt(currentUserID, 10),
		strconv.Itoa(page),
		strconv.Itoa(size),
		normalizeSearchMode(req),
		derefString(req.Keyword),
		authorID,
		derefString(req.Username),
		derefString(req.CategoryName),
		derefString(req.SubCategoryName),
		derefString(req.StartDate),
		derefString(req.EndDate),
		boolFlag(req.EnableVector),
		boolFlag(req.EnableGraph),
		boolFlag(req.Explain),
	)
}

// boolFlag 把可选布尔参数渲染成缓存键片段，缺省值用 d 表示
func boolFlag(value *bool) string {
	if value == nil {
		return "d"
	}
	if *value {
		return "1"
	}
	return "0"
}

// publishSearchLog 把搜索行为投递到消息队列，投递失败只记录日志
func (l *SearchArticlesLogic) publishSearchLog(req *types.SearchArticlesReq, page int, size int, currentUserID int64) {
	keyword := derefString(req.Keyword)
	if keyword == "" {
		return
	}

	logUserID := currentUserID
	if logUserID <= 0 && req.UserId != nil {
		logUserID = int64(*req.UserId)
	}

	msg := map[string]any{
		"action": "search",
		"userId": logUserID,
		"content": search.ArticleSearchDTO{
			Keyword:         keyword,
			UserID:          req.UserId,
			Username:        derefString(req.Username),
			CategoryName:    derefString(req.CategoryName),
			SubCategoryName: derefString(req.SubCategoryName),
			StartDate:       req.StartDate,
			EndDate:         req.EndDate,
			Page:            page,
			Size:            size,
		},
		"msg": constants.SEARCH_MSG,
	}
	if err := l.svcCtx.RabbitMQPublisher.PublishJSON(constants.ARTICLE_LOG_QUEUE, msg); err != nil {
		l.Errorf(constants.SEARCH_ERR+": %v", err)
	}
}

// appendGraphRecallItems 把图谱扩召回返回、但不在 ES 候选集内的文章按 id 补齐到候选集
// 补入条数以 SEARCH_GRAPH_RECALL_MAX 为上限，total 始终由 ES 决定
func (l *SearchArticlesLogic) appendGraphRecallItems(items []types.ArticleEsItem, graphItems []fastapiClient.GraphEnhanceItem) []types.ArticleEsItem {
	if len(graphItems) == 0 {
		return items
	}

	existing := make(map[int64]struct{}, len(items))
	for i := range items {
		existing[items[i].Id] = struct{}{}
	}

	extraIDs := make([]int64, 0, constants.SEARCH_GRAPH_RECALL_MAX)
	for i := range graphItems {
		articleID := graphItems[i].ArticleID
		if articleID <= 0 {
			continue
		}
		if _, ok := existing[articleID]; ok {
			continue
		}
		existing[articleID] = struct{}{}
		extraIDs = append(extraIDs, articleID)
		if len(extraIDs) >= constants.SEARCH_GRAPH_RECALL_MAX {
			break
		}
	}

	if len(extraIDs) == 0 {
		return items
	}

	extraArticles, err := l.svcCtx.SearchModel.GetArticlesByIDs(l.ctx, extraIDs)
	if err != nil {
		l.Warningf(constants.SEARCH_GRAPH_RECALL_DEGRADE_LOG, len(extraIDs), err)
		return items
	}

	return append(items, toArticleEsItems(extraArticles)...)
}

// toArticleEsItems 把 ES 文档转换为接口返回的文章项
func toArticleEsItems(articles []search.ArticleES) []types.ArticleEsItem {
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
	return items
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

// limitArticleIDs 将文章 ID 列表截断到指定数量上限
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

// clearExplainFields 清空结果中的解释字段，未开启 explain 时用于精简响应
func clearExplainFields(items []types.ArticleEsItem) {
	for i := range items {
		items[i].Reason = ""
		items[i].SemanticReason = ""
		items[i].Relations = make([]types.GraphRelation, 0)
		items[i].MatchedChunks = make([]types.VectorMatchedChunk, 0)
	}
}

// getCurrentUserFromContext 从请求上下文中读取当前登录用户的 ID 与用户名
func getCurrentUserFromContext(ctx context.Context) (int64, string) {
	userID, _ := ctx.Value(keys.UserIDKey).(int64)
	username, _ := ctx.Value(keys.UsernameKey).(string)
	return userID, username
}
