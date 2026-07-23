package search

import (
	"context"
	"encoding/json"
	"strings"
	"time"

	"github.com/olivere/elastic/v7"
)

const (
	articlesIndexName      = "articles"
	searchHistoryTableName = "articlelogs"
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
		layout := "2006-01-02 15:04:05"
		if searchDTO.StartDate != nil {
			if startTime, err := time.ParseInLocation(layout, *searchDTO.StartDate, time.Local); err == nil {
				rangeQuery.Gte(startTime.Format(layout))
			}
		}
		if searchDTO.EndDate != nil {
			if endTime, err := time.ParseInLocation(layout, *searchDTO.EndDate, time.Local); err == nil {
				rangeQuery.Lte(endTime.Format(layout))
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

	// 使用从 FastAPI 获取的 ES Painless 脚本模板，通过 Param 传入权重值
	// 参数名从 FastAPI 的脚本参数映射动态获取
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

	scriptScoreQuery := elastic.NewScriptScoreQuery(boolQuery, scoreScript)

	searchService := m.esClient.Search().
		Index(articlesIndexName).
		Query(scriptScoreQuery).
		From(from).
		Size(size).
		RequestCache(true)

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

	if len(articles) > 0 && m.articlesModel != nil && m.likesModel != nil && m.collectsModel != nil && m.focusModel != nil {
		viewsMap, err := m.articlesModel.GetArticleViewsByIDs(ctx, articleIDs)
		if err != nil {
			return nil, 0, err
		}

		likeCounts, err := m.likesModel.GetLikeCountsByArticleIDs(ctx, articleIDs)
		if err != nil {
			return nil, 0, err
		}

		collectCounts, err := m.collectsModel.GetCollectCountsByArticleIDs(ctx, articleIDs)
		if err != nil {
			return nil, 0, err
		}

		authorUserIDs := make([]int64, 0, len(articles))
		for _, article := range articles {
			authorUserIDs = append(authorUserIDs, article.UserID)
		}

		authorFollowCounts, err := m.focusModel.GetFollowCountsByUserIDs(ctx, authorUserIDs)
		if err != nil {
			return nil, 0, err
		}

		for i := range articles {
			if views, ok := viewsMap[articles[i].ID]; ok {
				articles[i].Views = int(views)
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
