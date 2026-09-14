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
	if searchDTO.Keyword == "" {
		searchService = searchService.Sort("create_at", false)
	}

	if searchDTO.Keyword != "" {
		highlight := elastic.NewHighlight().PreTags("<em>").PostTags("</em>").
			Fields(
				elastic.NewHighlighterField("title"),
				elastic.NewHighlighterField("content"),
				elastic.NewHighlighterField("tags"),
			).
			FragmentSize(150)
		searchService = searchService.Highlight(highlight)
	}

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

		var viewsResult, likeResult, collectResult, followResult client.Result
		var viewsErr, likeErr, collectErr, followErr error

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
		)

		// 回填失败的指标跳过覆盖，保留 ES 文档原值作为降级，不阻断搜索主链路
		degraded := make([]string, 0, 4)
		if viewsErr != nil {
			degraded = append(degraded, "views")
		}
		if likeErr != nil {
			degraded = append(degraded, "likes")
		}
		if collectErr != nil {
			degraded = append(degraded, "collects")
		}
		if followErr != nil {
			degraded = append(degraded, "author_follows")
		}
		if len(degraded) > 0 {
			degradeErr := viewsErr
			if degradeErr == nil {
				degradeErr = likeErr
			}
			if degradeErr == nil {
				degradeErr = collectErr
			}
			if degradeErr == nil {
				degradeErr = followErr
			}
			logx.WithContext(ctx).Slow("[WARN] " + fmt.Sprintf(constants.SEARCH_STATS_FILL_DEGRADE_LOG, strings.Join(degraded, ","), degradeErr))
		}

		viewsMap, _ := springClient.ParseArticleViewsMap(viewsResult)
		likeCounts, _ := springClient.ParseCountsMap(likeResult)
		collectCounts, _ := springClient.ParseCountsMap(collectResult)
		authorFollowCounts, _ := springClient.ParseCountsMap(followResult)

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
