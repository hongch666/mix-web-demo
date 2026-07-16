// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package search

import (
	"context"
	"encoding/json"
	"fmt"
	"math"
	"strings"

	"app/common/constants"
	"app/common/exceptions"
	"app/common/keys"
	"app/common/utils"
	"app/internal/cache"
	"app/internal/client/fastapiClient"
	"app/internal/logic/search/graphreason"
	"app/internal/logic/search/vectorreason"
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
	page := req.Page
	if page < 1 {
		page = 1
	}
	size := req.Size
	if size < 1 {
		size = 10
	}

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
	isLoggedIn := currentUserID > 0

	// ═══════════ Step 1: 并行获取权重 + 嵌入向量 + 用户图谱特征 ═══════
	var weights fastapiClient.SearchWeights
	var queryVector []float64
	var userFeatures *cache.UserGraphFeatures

	err = mr.Finish(
		func() error {
			w, err := l.svcCtx.FastapiClient.GetSearchWeights(l.ctx)
			if err != nil {
				return err
			}
			weights = w
			return nil
		},
		func() error {
			if keyword == "" || !l.svcCtx.Config.Search.EmbedEnabled {
				return nil
			}
			qv, err := l.svcCtx.FastapiClient.GetQueryEmbedding(l.ctx, keyword)
			if err != nil {
				l.Warningf(constants.SEARCH_EMBED_FAIL, err)
				return nil
			}
			queryVector = qv
			return nil
		},
		func() error {
			if currentUserID <= 0 || !l.svcCtx.Config.Search.GraphEnabled {
				return nil
			}
			uf, err := cache.GetUserGraphFeatures(l.ctx, l.svcCtx.RedisClient, currentUserID)
			if err != nil {
				l.Warningf(constants.SEARCH_GRAPH_FEATURE_FAIL, err)
				return nil
			}
			userFeatures = uf
			return nil
		},
	)
	if err != nil {
		return nil, exceptions.NewInternalServerError(constants.SEARCH_PREPARE_FAIL, err.Error())
	}

	// ═══════════ Step 2: 构建 ES 查询参数 ═══════
	esParams := buildESQueryParams(
		keyword, weights, queryVector, userFeatures,
		types.NormalizeSearchMode(req),
		isLoggedIn,
	)

	searchDTO := search.ArticleSearchDTO{
		Keyword:         keyword,
		UserID:          req.UserId,
		Username:        username,
		CategoryName:    categoryName,
		SubCategoryName: subCategoryName,
		StartDate:       req.StartDate,
		EndDate:         req.EndDate,
		Page:            page,
		Size:            size,
	}

	articles, total, err := l.svcCtx.SearchModel.SearchArticle(l.ctx, searchDTO, &search.ArticleSearchParams{
		ES: &search.ESScoringParams{
			EsWeight:            esParams.EsWeight,
			AiWeight:            esParams.AiWeight,
			UserWeight:          esParams.UserWeight,
			ViewsWeight:         esParams.ViewsWeight,
			LikesWeight:         esParams.LikesWeight,
			CollectsWeight:      esParams.CollectsWeight,
			FollowWeight:        esParams.FollowWeight,
			RecencyWeight:       esParams.RecencyWeight,
			MaxViewsNorm:        esParams.MaxViewsNorm,
			MaxLikesNorm:        esParams.MaxLikesNorm,
			MaxCollectsNorm:     esParams.MaxCollectsNorm,
			MaxFollowsNorm:      esParams.MaxFollowsNorm,
			DecayDaysSq:         esParams.DecayDaysSq,
			VectorWeight:        esParams.VectorWeight,
			QueryVector:         esParams.QueryVector,
			GraphInterestWeight: esParams.GraphInterestWeight,
			GraphFollowWeight:   esParams.GraphFollowWeight,
			GraphSubcatWeight:   esParams.GraphSubcatWeight,
			GraphKeywordWeight:  esParams.GraphKeywordWeight,
			UserTagList:         esParams.UserTagList,
			FollowedAuthorIds:   esParams.FollowedAuthorIds,
			PreferredSubCatIds:  esParams.PreferredSubCatIds,
			KeywordTags:         esParams.KeywordTags,
		},
	})
	if err != nil {
		l.Error(fmt.Sprintf(constants.SEARCH_EXECUTION_ERROR+": %v", err))
		return nil, exceptions.NewInternalServerError(constants.SEARCH_EXECUTION_ERROR, err.Error())
	}

	l.Info(constants.ARTICLE_SEARCH_SUCCESS)

	// ═══════════ Step 3: MySQL 回填 + matched_chunks 并行获取 ═══
	// MySQL 回填已在 es.go 中完成
	// matched_chunks 从 FastAPI 获取 (仅用于展示, 不参与排序)
	var matchedChunksMap map[int64][]types.VectorMatchedChunk

	if keyword != "" {
		articleIDs := make([]int64, 0, len(articles))
		for _, a := range articles {
			articleIDs = append(articleIDs, a.ID)
		}
		chunks, chunkErr := l.svcCtx.FastapiClient.GetMatchedChunks(l.ctx, articleIDs, keyword)
		if chunkErr != nil {
			l.Warningf(constants.SEARCH_MATCHED_CHUNKS_FAIL, chunkErr)
			matchedChunksMap = make(map[int64][]types.VectorMatchedChunk)
		} else {
			matchedChunksMap = chunks
		}
	} else {
		matchedChunksMap = make(map[int64][]types.VectorMatchedChunk)
	}

	// ═══════════ Step 3.5: 信号4 候选间相似度补算 ═══
	fillCandidateSimScores(articles)

	// ═══════════ Step 4: 组装响应 ═══════
	items := make([]types.ArticleEsItem, len(articles))
	for i, art := range articles {
		items[i] = types.ArticleEsItem{
			Id:                art.ID,
			Title:             art.Title,
			Content:           art.Content,
			UserId:            art.UserID,
			Username:          art.Username,
			Tags:              art.Tags,
			Status:            art.Status,
			Views:             art.Views,
			LikeCount:         art.LikeCount,
			CollectCount:      art.CollectCount,
			AuthorFollowCount: art.AuthorFollowCount,
			CategoryName:      art.CategoryName,
			SubCategoryName:   art.SubCategoryName,
			CreateAt:          art.CreateAt,
			UpdateAt:          art.UpdateAt,
			AiScore:           art.AIScore,
			UserScore:         art.UserScore,
			AiCommentCount:    art.AICommentCount,
			UserCommentCount:  art.UserCommentCount,
		}

		// 打分字段
		items[i].EsScore = roundTo4(art.TradScore)
		items[i].VectorScore = roundTo4(art.VecScore)
		items[i].GraphScore = roundTo4(userGraphScore(art, userFeatures))
		items[i].FinalScore = roundTo4(art.FinalScore)

		// 解释字段
		items[i].Reason = graphreason.Generate(art.ID, art.UserID, art.Username, art.Tags, art.SubCategoryName, userFeatures)
		items[i].SemanticReason = vectorreason.Generate(art.VecScore)
		items[i].Relations = graphreason.BuildRelations(art.ID, art.UserID, art.Tags, userFeatures)

		if chunks, ok := matchedChunksMap[art.ID]; ok {
			items[i].MatchedChunks = chunks
		} else {
			items[i].MatchedChunks = make([]types.VectorMatchedChunk, 0)
		}

		items[i].ScoreDetails = types.ScoreDetails{
			EsScore:       roundTo4(art.TradScore),
			VectorScore:   roundTo4(art.VecScore),
			GraphScore:    roundTo4(items[i].GraphScore),
			BusinessScore: 0,
			RecencyScore:  0,
		}
	}

	if !types.IsExplainEnabled(req) {
		clearExplainFields(items)
	}

	resp = &types.SearchArticlesResp{Total: total, List: items}

	// ═══════════ Step 5: RabbitMQ 搜索日志 ═══
	if req.Keyword != nil && *req.Keyword != "" {
		logUserID := currentUserID
		if logUserID <= 0 && req.UserId != nil {
			logUserID = int64(*req.UserId)
		}
		msg := map[string]any{
			"action":  "search",
			"userId":  logUserID,
			"content": searchDTO,
			"msg":     constants.SEARCH_MSG,
		}
		jsonBytes, err := json.Marshal(msg)
		if err != nil {
			l.Error(fmt.Sprintf(constants.SEARCH_ERR+": %v", err))
		} else {
			if l.svcCtx.RabbitMQPublisher != nil {
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
	}

	return
}

// userGraphScore 图谱总分 (ES 已算信号1/2/3/5 + GoZero 补算信号4)
func userGraphScore(art search.ArticleESWithScores, uf *cache.UserGraphFeatures) float64 {
	total := art.GraphScore + art.CandidateSimScore
	return clamp01(total)
}

// fillCandidateSimScores 信号4：候选间标签相似度
func fillCandidateSimScores(articles []search.ArticleESWithScores) {
	tagFreq := make(map[string]int)
	for _, a := range articles {
		for _, tag := range strings.Split(a.Tags, ",") {
			tag = strings.TrimSpace(tag)
			if tag != "" {
				tagFreq[tag]++
			}
		}
	}
	for i := range articles {
		shared := 0
		for _, tag := range strings.Split(articles[i].Tags, ",") {
			tag = strings.TrimSpace(tag)
			if tagFreq[tag] > 1 {
				shared++
			}
		}
		articles[i].CandidateSimScore = math.Min(float64(shared)/3.0, 1.0) * 0.04
	}
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
