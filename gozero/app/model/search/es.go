package search

import (
	"context"
	"encoding/json"
	"strings"
	"time"

	"app/common/constants"

	"github.com/olivere/elastic/v7"
)

const (
	articlesIndexName      = "articles"
	searchHistoryTableName = "articlelogs"
)

func (m *searchModel) SearchArticle(ctx context.Context, searchDTO ArticleSearchDTO, params *ArticleSearchParams) ([]ArticleESWithScores, int, error) {
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
		boolQuery.Filter(elastic.NewTermQuery("userId", *searchDTO.UserID))
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

	// 全量13项 script_score
	scoreScript := elastic.NewScript(constants.ES_SEARCH_SCRIPT).
		Param(constants.ES_WEIGHT_NAME, params.ES.EsWeight).
		Param(constants.AI_RATING_WEIGHT_NAME, params.ES.AiWeight).
		Param(constants.USER_RATING_WEIGHT_NAME, params.ES.UserWeight).
		Param(constants.VIEWS_WEIGHT_NAME, params.ES.ViewsWeight).
		Param(constants.LIKES_WEIGHT_NAME, params.ES.LikesWeight).
		Param(constants.COLLECTS_WEIGHT_NAME, params.ES.CollectsWeight).
		Param(constants.AUTHOR_FOLLOW_WEIGHT_NAME, params.ES.FollowWeight).
		Param(constants.RECENCY_WEIGHT_NAME, params.ES.RecencyWeight).
		Param(constants.RECENCY_DECAY_DAYS_NAME, params.ES.DecayDaysSq).
		Param(constants.MAX_VIEWS_NORMALIZED_NAME, params.ES.MaxViewsNorm).
		Param(constants.MAX_LIKES_NORMALIZED_NAME, params.ES.MaxLikesNorm).
		Param(constants.MAX_COLLECTS_NORMALIZED_NAME, params.ES.MaxCollectsNorm).
		Param(constants.MAX_FOLLOWS_NORMALIZED_NAME, params.ES.MaxFollowsNorm).
		Param("queryVector", params.ES.QueryVector).
		Param("vectorWeight", params.ES.VectorWeight).
		Param("userTagList", params.ES.UserTagList).
		Param("followedAuthorIds", params.ES.FollowedAuthorIds).
		Param("preferredSubCatIds", params.ES.PreferredSubCatIds).
		Param("keywordTags", params.ES.KeywordTags).
		Param("graphInterestWeight", params.ES.GraphInterestWeight).
		Param("graphFollowWeight", params.ES.GraphFollowWeight).
		Param("graphSubcatWeight", params.ES.GraphSubcatWeight).
		Param("graphKeywordWeight", params.ES.GraphKeywordWeight)

	scriptScoreQuery := elastic.NewScriptScoreQuery(boolQuery, scoreScript)

	querySource, _ := scriptScoreQuery.Source()

	// 构建完整 search body, 含 script_fields
	body := map[string]interface{}{
		"query":        querySource,
		"from":         from,
		"size":         size,
		"request_cache": true,
		"script_fields": map[string]interface{}{
			"trad_score": map[string]interface{}{
				"script": map[string]interface{}{
					"source": constants.ES_TRAD_SCORE_SCRIPT,
					"params": map[string]interface{}{
						constants.ES_WEIGHT_NAME:               params.ES.EsWeight,
						constants.AI_RATING_WEIGHT_NAME:        params.ES.AiWeight,
						constants.USER_RATING_WEIGHT_NAME:      params.ES.UserWeight,
						constants.VIEWS_WEIGHT_NAME:            params.ES.ViewsWeight,
						constants.LIKES_WEIGHT_NAME:            params.ES.LikesWeight,
						constants.COLLECTS_WEIGHT_NAME:         params.ES.CollectsWeight,
						constants.AUTHOR_FOLLOW_WEIGHT_NAME:    params.ES.FollowWeight,
						constants.RECENCY_WEIGHT_NAME:          params.ES.RecencyWeight,
						constants.RECENCY_DECAY_DAYS_NAME:      params.ES.DecayDaysSq,
						constants.MAX_VIEWS_NORMALIZED_NAME:    params.ES.MaxViewsNorm,
						constants.MAX_LIKES_NORMALIZED_NAME:    params.ES.MaxLikesNorm,
						constants.MAX_COLLECTS_NORMALIZED_NAME: params.ES.MaxCollectsNorm,
						constants.MAX_FOLLOWS_NORMALIZED_NAME:  params.ES.MaxFollowsNorm,
					},
				},
			},
			"vec_score": map[string]interface{}{
				"script": map[string]interface{}{
					"source": constants.ES_VEC_SCORE_SCRIPT,
					"params": map[string]interface{}{
						"qv": params.ES.QueryVector,
					},
				},
			},
			"graph_score": map[string]interface{}{
				"script": map[string]interface{}{
					"source": constants.ES_GRAPH_SCORE_SCRIPT,
					"params": map[string]interface{}{
						"utl": params.ES.UserTagList,
						"fai": params.ES.FollowedAuthorIds,
						"psi": params.ES.PreferredSubCatIds,
						"kwt": params.ES.KeywordTags,
						"giw": params.ES.GraphInterestWeight,
						"gfw": params.ES.GraphFollowWeight,
						"gsw": params.ES.GraphSubcatWeight,
						"gkw": params.ES.GraphKeywordWeight,
					},
				},
			},
		},
	}

	if searchDTO.Keyword != "" {
		body["highlight"] = map[string]interface{}{
			"pre_tags":  []string{"<em>"},
			"post_tags": []string{"</em>"},
			"fields": map[string]interface{}{
				"title":   map[string]interface{}{"fragment_size": 150},
				"content": map[string]interface{}{"fragment_size": 150},
				"tags":    map[string]interface{}{"fragment_size": 150},
			},
		}
	}

	searchService := m.esClient.Search().Index(articlesIndexName).Source(body)

	searchResult, err := searchService.Do(ctx)
	if err != nil {
		return nil, 0, err
	}

	if searchResult.Hits == nil {
		return nil, 0, ErrSearchHitsEmpty
	}

	articles := make([]ArticleESWithScores, 0, len(searchResult.Hits.Hits))
	articleIDs := make([]int64, 0, len(searchResult.Hits.Hits))

	for _, hit := range searchResult.Hits.Hits {
		var article ArticleES
		if err = json.Unmarshal(hit.Source, &article); err != nil {
			return nil, 0, err
		}

		as := ArticleESWithScores{ArticleES: article}

		// _score = 全量复合分
		if hit.Score != nil {
			as.FinalScore = *hit.Score
		}

		// script_fields 子分
		if hit.Fields != nil {
			as.TradScore = extractFloatField(hit.Fields, "trad_score")
			as.VecScore = extractFloatField(hit.Fields, "vec_score")
			as.GraphScore = extractFloatField(hit.Fields, "graph_score")
		}

		if hit.Highlight != nil {
			if hs, ok := hit.Highlight["title"]; ok && len(hs) > 0 {
				as.Title = strings.Join(hs, " ")
			}
			if hs, ok := hit.Highlight["content"]; ok && len(hs) > 0 {
				as.Content = strings.Join(hs, " ")
			}
			if hs, ok := hit.Highlight["tags"]; ok && len(hs) > 0 {
				as.Tags = strings.Join(hs, " ")
			}
		}

		articles = append(articles, as)
		articleIDs = append(articleIDs, as.ID)
	}

	if len(articles) > 0 && m.articlesModel != nil && m.likesModel != nil && m.collectsModel != nil && m.focusModel != nil {
		viewsMap, err1 := m.articlesModel.GetArticleViewsByIDs(ctx, articleIDs)
		if err1 != nil {
			return nil, 0, err1
		}
		likeCounts, err2 := m.likesModel.GetLikeCountsByArticleIDs(ctx, articleIDs)
		if err2 != nil {
			return nil, 0, err2
		}
		collectCounts, err3 := m.collectsModel.GetCollectCountsByArticleIDs(ctx, articleIDs)
		if err3 != nil {
			return nil, 0, err3
		}
		authorUserIDs := make([]int64, 0, len(articles))
		for _, a := range articles {
			authorUserIDs = append(authorUserIDs, a.UserID)
		}
		authorFollowCounts, err4 := m.focusModel.GetFollowCountsByUserIDs(ctx, authorUserIDs)
		if err4 != nil {
			return nil, 0, err4
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

func extractFloatField(fields interface{}, name string) float64 {
	m, ok := fields.(map[string]interface{})
	if !ok {
		return 0
	}
	vals, ok := m[name].([]interface{})
	if !ok || len(vals) == 0 {
		return 0
	}
	if v, ok := vals[0].(float64); ok {
		return v
	}
	return 0
}
