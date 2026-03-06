package search

import (
	"app/common/utils"
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

func (m *searchModel) SearchArticle(ctx context.Context, searchDTO ArticleSearchDTO) ([]ArticleES, int, error) {
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

	scoreScript := elastic.NewScript(utils.ES_SEARCH_SCRIPT).
		Param(utils.ES_WEIGHT_NAME, m.config.ESScoreWeight).
		Param(utils.AI_RATING_WEIGHT_NAME, m.config.AIRatingWeight).
		Param(utils.USER_RATING_WEIGHT_NAME, m.config.UserRatingWeight).
		Param(utils.VIEWS_WEIGHT_NAME, m.config.ViewsWeight).
		Param(utils.LIKES_WEIGHT_NAME, m.config.LikesWeight).
		Param(utils.COLLECTS_WEIGHT_NAME, m.config.CollectsWeight).
		Param(utils.AUTHOR_FOLLOW_WEIGHT_NAME, m.config.AuthorFollowWeight).
		Param(utils.RECENCY_WEIGHT_NAME, m.config.RecencyWeight).
		Param(utils.RECENCY_DECAY_DAYS_NAME, float64(m.config.RecencyDecayDays)*float64(m.config.RecencyDecayDays)).
		Param(utils.MAX_VIEWS_NORMALIZED_NAME, m.config.MaxViewsNormalized).
		Param(utils.MAX_LIKES_NORMALIZED_NAME, m.config.MaxLikesNormalized).
		Param(utils.MAX_COLLECTS_NORMALIZED_NAME, m.config.MaxCollectsNormalized).
		Param(utils.MAX_FOLLOWS_NORMALIZED_NAME, m.config.MaxFollowsNormalized)

	scriptScoreQuery := elastic.NewScriptScoreQuery(boolQuery, scoreScript)

	searchService := m.esClient.Search().
		Index(articlesIndexName).
		Query(scriptScoreQuery).
		From(from).
		Size(size)

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
