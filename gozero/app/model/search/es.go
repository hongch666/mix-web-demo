package search

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"app/common/client"
	"app/common/constants"
	"app/internal/client/springClient"

	"github.com/olivere/elastic/v7"
	"github.com/zeromicro/go-zero/core/logx"
	"github.com/zeromicro/go-zero/core/mr"
)

const (
	articlesIndexName = "articles"
)

// SearchArticle 按关键词与过滤条件检索文章索引，支持脚本复合打分与高亮，并用 Spring 实时统计覆盖 ES 快照数据
func (m *searchModel) SearchArticle(ctx context.Context, searchDTO ArticleSearchDTO, esScript string, weights *SearchWeights, paramMap ScriptParamMapping) ([]ArticleES, int, error) {
	if m.esClient == nil {
		return nil, 0, ErrNilESClient
	}

	boolQuery := elastic.NewBoolQuery()

	if searchDTO.Keyword != "" {
		multiMatch := elastic.NewMultiMatchQuery(searchDTO.Keyword, "title", "content", "tags").Type("best_fields").Operator("and")
		boolQuery.Must(multiMatch)
	}

	boolQuery.Filter(elastic.NewTermQuery("status", 1))

	if searchDTO.UserID != nil {
		boolQuery.Filter(elastic.NewTermQuery("user_id", *searchDTO.UserID))
	}

	if searchDTO.Username != "" {
		boolQuery.Filter(elastic.NewWildcardQuery("username", "*"+searchDTO.Username+"*"))
	}

	if searchDTO.CategoryName != "" {
		boolQuery.Filter(elastic.NewTermQuery("category_name", searchDTO.CategoryName))
	}

	if searchDTO.SubCategoryName != "" {
		boolQuery.Filter(elastic.NewTermQuery("sub_category_name", searchDTO.SubCategoryName))
	}

	if searchDTO.StartDate != nil || searchDTO.EndDate != nil {
		rangeQuery := elastic.NewRangeQuery("create_at")
		if searchDTO.StartDate != nil {
			if startTime, err := time.ParseInLocation(constants.DateTimeFormat, *searchDTO.StartDate, time.Local); err == nil {
				rangeQuery.Gte(startTime.Format(constants.DateTimeFormat))
			}
		}
		if searchDTO.EndDate != nil {
			if endTime, err := time.ParseInLocation(constants.DateTimeFormat, *searchDTO.EndDate, time.Local); err == nil {
				rangeQuery.Lte(endTime.Format(constants.DateTimeFormat))
			}
		}
		boolQuery.Filter(rangeQuery)
	}

	page := searchDTO.Page
	if page < 1 {
		page = 1
	}
	size := searchDTO.Size
	if size < 1 {
		size = 10
	}
	from := (page - 1) * size

	// 脚本模板与权重齐备时走 ScriptScoreQuery 复合打分
	// 任一缺失说明 FastAPI 侧脚本三件套获取失败，此处退化为普通条件查询，只依赖 BM25 相关度
	var finalQuery elastic.Query = boolQuery
	if esScript != "" && weights != nil {
		scoreScript := elastic.NewScript(esScript).
			Param(getParamName(paramMap, "es_score_weight"), weights.ESScoreWeight).
			Param(getParamName(paramMap, "ai_rating_weight"), weights.AIRatingWeight).
			Param(getParamName(paramMap, "user_rating_weight"), weights.UserRatingWeight).
			Param(getParamName(paramMap, "views_weight"), weights.ViewsWeight).
			Param(getParamName(paramMap, "likes_weight"), weights.LikesWeight).
			Param(getParamName(paramMap, "collects_weight"), weights.CollectsWeight).
			Param(getParamName(paramMap, "author_follow_weight"), weights.AuthorFollowWeight).
			Param(getParamName(paramMap, "recency_weight"), weights.RecencyWeight).
			Param(getParamName(paramMap, "recency_decay_days"), float64(weights.RecencyDecayDays)*float64(weights.RecencyDecayDays)).
			Param(getParamName(paramMap, "max_views_normalized"), weights.MaxViewsNormalized).
			Param(getParamName(paramMap, "max_likes_normalized"), weights.MaxLikesNormalized).
			Param(getParamName(paramMap, "max_collects_normalized"), weights.MaxCollectsNormalized).
			Param(getParamName(paramMap, "max_follows_normalized"), weights.MaxFollowsNormalized)
		finalQuery = elastic.NewScriptScoreQuery(boolQuery, scoreScript)
	}

	searchService := m.esClient.Search().
		Index(articlesIndexName).
		Query(finalQuery).
		From(from).
		Size(size).
		RequestCache(true)

	// 无关键词时 boolQuery 只含过滤条件，_score 恒为 0，需显式按创建时间倒序保证顺序确定
	sortByCreateAt := searchDTO.Keyword == ""
	if sortByCreateAt {
		searchService = searchService.Sort("create_at", false)
	}

	var highlight *elastic.Highlight
	if searchDTO.Keyword != "" {
		highlight = elastic.NewHighlight().PreTags("<em>").PostTags("</em>").
			Fields(
				elastic.NewHighlighterField("title"),
				elastic.NewHighlighterField("content"),
				elastic.NewHighlighterField("tags"),
			).
			FragmentSize(150)
		searchService = searchService.Highlight(highlight)
	}

	// DSL 日志开关关闭时该调用直接返回，不产生任何序列化开销
	m.logSearchDSL(ctx, finalQuery, from, size, sortByCreateAt, highlight)

	searchResult, err := searchService.Do(ctx)
	if err != nil {
		return nil, 0, err
	}

	if searchResult.Hits == nil {
		return nil, 0, ErrSearchHitsEmpty
	}

	articles := make([]ArticleES, 0, len(searchResult.Hits.Hits))
	articleIDs := make([]int64, 0, len(searchResult.Hits.Hits))

	for _, hit := range searchResult.Hits.Hits {
		var article ArticleES
		if err = json.Unmarshal(hit.Source, &article); err != nil {
			return nil, 0, err
		}

		// 记录 ES 原始评分
		if hit.Score != nil {
			article.ESScore = *hit.Score
		}

		if hit.Highlight != nil {
			if hs, ok := hit.Highlight["title"]; ok && len(hs) > 0 {
				article.Title = strings.Join(hs, " ")
			}
			if hs, ok := hit.Highlight["content"]; ok && len(hs) > 0 {
				article.Content = strings.Join(hs, " ")
			}
			if hs, ok := hit.Highlight["tags"]; ok && len(hs) > 0 {
				article.Tags = strings.Join(hs, " ")
			}
		}

		articles = append(articles, article)
		articleIDs = append(articleIDs, article.ID)
	}

	if len(articles) > 0 && m.springClient != nil {
		authorUserIDs := make([]int64, 0, len(articles))
		for _, article := range articles {
			authorUserIDs = append(authorUserIDs, article.UserID)
		}

		// ES 文档里的阅读量、点赞、收藏、粉丝与评分都是同步快照
		// 检索时统一用 Spring 实时值覆盖，失败则保留 ES 文档原值作为降级
		var viewsResult, likeResult, collectResult, followResult, commentScoreResult client.Result
		var viewsErr, likeErr, collectErr, followErr, commentScoreErr error

		_ = mr.Finish(
			func() error {
				viewsResult, viewsErr = m.springClient.GetArticleViewsByIDs(ctx, articleIDs)
				return viewsErr
			},
			func() error {
				likeResult, likeErr = m.springClient.GetLikeCountsByArticleIDs(ctx, articleIDs)
				return likeErr
			},
			func() error {
				collectResult, collectErr = m.springClient.GetCollectCountsByArticleIDs(ctx, articleIDs)
				return collectErr
			},
			func() error {
				followResult, followErr = m.springClient.GetFollowCountsByUserIDs(ctx, authorUserIDs)
				return followErr
			},
			func() error {
				commentScoreResult, commentScoreErr = m.springClient.GetCommentScoresByArticleIDs(ctx, articleIDs)
				return commentScoreErr
			},
		)

		viewsMap, viewsParseErr := springClient.ParseArticleViewsMap(viewsResult)
		likeCounts, likeParseErr := springClient.ParseCountsMap(likeResult)
		collectCounts, collectParseErr := springClient.ParseCountsMap(collectResult)
		authorFollowCounts, followParseErr := springClient.ParseCountsMap(followResult)
		commentScores, commentParseErr := springClient.ParseCommentScoresMap(
			commentScoreResult,
		)

		// 回填失败的指标跳过覆盖，保留 ES 文档原值作为降级，不阻断搜索主链路
		// 调用失败与响应结构不符契约（解析失败）一并计入：解析静默失败会让统计与评分长期显示 ES 旧值
		metrics := constants.SEARCH_STATS_FILL_METRICS
		fillErrors := []error{
			firstError(viewsErr, viewsParseErr),
			firstError(likeErr, likeParseErr),
			firstError(collectErr, collectParseErr),
			firstError(followErr, followParseErr),
			firstError(commentScoreErr, commentParseErr),
		}
		degraded := make([]string, 0, len(metrics))
		for i, fillErr := range fillErrors {
			if fillErr != nil {
				degraded = append(degraded, metrics[i])
			}
		}
		if len(degraded) > 0 {
			logx.WithContext(ctx).Slow("[WARN] " + fmt.Sprintf(constants.SEARCH_STATS_FILL_DEGRADE_LOG, strings.Join(degraded, ","), firstError(fillErrors...)))
		}

		for i := range articles {
			if views, ok := viewsMap[articles[i].ID]; ok {
				articles[i].Views = views
			}
			if likes, ok := likeCounts[articles[i].ID]; ok {
				articles[i].LikeCount = int(likes)
			}
			if collects, ok := collectCounts[articles[i].ID]; ok {
				articles[i].CollectCount = int(collects)
			}
			if followCount, ok := authorFollowCounts[articles[i].UserID]; ok {
				articles[i].AuthorFollowCount = int(followCount)
			}
			applyCommentScores(&articles[i], commentScores[articles[i].ID])
		}
	}

	total := int(searchResult.Hits.TotalHits.Value)
	return articles, total, nil
}

// getParamName 从脚本参数映射中获取参数名，返回 FastAPI 定义的脚本参数名
// paramMap: 从 FastAPI 获取的 weight_key → param_name 映射
// weightKey: FastAPI 定义的权重 key
func getParamName(paramMap ScriptParamMapping, weightKey string) string {
	if paramMap != nil {
		if name, ok := paramMap[weightKey]; ok && name != "" {
			return name
		}
	}
	return weightKey
}

// firstError 返回第一个非空错误，用于降级日志记录失败原因
func firstError(errs ...error) error {
	for _, err := range errs {
		if err != nil {
			return err
		}
	}
	return nil
}

// applyCommentScores 用 Spring 实时评分覆盖 ES 快照中的 AI 与用户评分及其评论数
// 某类评分缺失（没有该类评论或评分接口降级）时保留 ES 文档原值，与其它统计字段口径一致
func applyCommentScores(article *ArticleES, scores map[string]springClient.CommentScoreVO) {
	if aiScores, ok := scores["ai"]; ok {
		article.AIScore = aiScores.AverageScore
		article.AICommentCount = int(aiScores.Count)
	}
	if userScores, ok := scores["user"]; ok {
		article.UserScore = userScores.AverageScore
		article.UserCommentCount = int(userScores.Count)
	}
}
