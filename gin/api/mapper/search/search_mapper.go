package search

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/hongch666/mix-web-demo/gin/api/mapper/sync"
	"github.com/hongch666/mix-web-demo/gin/common/config"
	"github.com/hongch666/mix-web-demo/gin/common/exceptions"
	"github.com/hongch666/mix-web-demo/gin/common/utils"
	"github.com/hongch666/mix-web-demo/gin/entity/dto"
	"github.com/hongch666/mix-web-demo/gin/entity/po"

	"github.com/olivere/elastic/v7"
	"go.mongodb.org/mongo-driver/bson"
)

type SearchMapper struct{}

func (m *SearchMapper) SearchArticle(ctx context.Context, searchDTO dto.ArticleSearchDTO) ([]po.ArticleES, int) {
	boolQuery := elastic.NewBoolQuery()

	// 关键词多字段搜索
	if searchDTO.Keyword != "" {
		multiMatch := elastic.NewMultiMatchQuery(searchDTO.Keyword, "title", "content", "tags").
			Type("best_fields").
			Operator("and")
		boolQuery.Must(multiMatch)
	}

	// 过滤已发布的文章 status=1
	boolQuery.Filter(elastic.NewTermQuery("status", 1))

	// 用户ID过滤（可选）
	if searchDTO.UserID != nil {
		boolQuery.Filter(elastic.NewTermQuery("userId", *searchDTO.UserID))
	}

	// 用户名过滤（可选）
	if searchDTO.Username != "" {
		boolQuery.Filter(elastic.NewWildcardQuery("username", "*"+searchDTO.Username+"*"))
	}

	// 分类名称完全匹配过滤（可选）
	if searchDTO.CategoryName != "" {
		boolQuery.Filter(elastic.NewTermQuery("category_name", searchDTO.CategoryName))
	}

	// 子分类名称完全匹配过滤（可选）
	if searchDTO.SubCategoryName != "" {
		boolQuery.Filter(elastic.NewTermQuery("sub_category_name", searchDTO.SubCategoryName))
	}

	// 发布时间范围过滤（可选）
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

	// 分页参数
	page := searchDTO.Page
	if page < 1 {
		page = 1
	}
	size := searchDTO.Size
	if size < 1 {
		size = 10
	}
	from := (page - 1) * size

	// 执行搜索（使用script_score在ES层面进行评分计算）
	esClient := config.ESClient

	// 获取搜索权重配置
	searchCfg := config.Config.Search

	// 构建综合评分脚本：ES分数(sigmoid归一化) + AI评分 + 用户评分 + 阅读量 + 点赞量 + 收藏量 + 作者关注数 + 文章新鲜度
	// ES分数使用sigmoid函数进行归一化，确保分数在0-1范围内
	// 新鲜度计算：使用高斯衰减函数，30天内文章最新鲜度最高，随着时间增加而衰减
	scoreScript := elastic.NewScript(utils.ES_SEARCH_SCRIPT).
		Param(utils.ES_WEIGHT_NAME, searchCfg.ESScoreWeight).
		Param(utils.AI_RATING_WEIGHT_NAME, searchCfg.AIRatingWeight).
		Param(utils.USER_RATING_WEIGHT_NAME, searchCfg.UserRatingWeight).
		Param(utils.VIEWS_WEIGHT_NAME, searchCfg.ViewsWeight).
		Param(utils.LIKES_WEIGHT_NAME, searchCfg.LikesWeight).
		Param(utils.COLLECTS_WEIGHT_NAME, searchCfg.CollectsWeight).
		Param(utils.AUTHOR_FOLLOW_WEIGHT_NAME, searchCfg.AuthorFollowWeight).
		Param(utils.RECENCY_WEIGHT_NAME, searchCfg.RecencyWeight).
		Param(utils.RECENCY_DECAY_DAYS_NAME, float64(searchCfg.RecencyDecayDays)*float64(searchCfg.RecencyDecayDays)).
		Param(utils.MAX_VIEWS_NORMALIZED_NAME, searchCfg.MaxViewsNormalized).
		Param(utils.MAX_LIKES_NORMALIZED_NAME, searchCfg.MaxLikesNormalized).
		Param(utils.MAX_COLLECTS_NORMALIZED_NAME, searchCfg.MaxCollectsNormalized).
		Param(utils.MAX_FOLLOWS_NORMALIZED_NAME, searchCfg.MaxFollowsNormalized)

	// 使用script_score包装bool查询
	scriptScoreQuery := elastic.NewScriptScoreQuery(boolQuery, scoreScript)

	searchService := esClient.Search().
		Index("articles").
		Query(scriptScoreQuery).
		From(from).Size(size)

	// 如果有关键词，启用高亮
	if searchDTO.Keyword != "" {
		hl := elastic.NewHighlight().
			PreTags("<em>").PostTags("</em>")
		hl = hl.Fields(
			elastic.NewHighlighterField("title"),
			elastic.NewHighlighterField("content"),
			elastic.NewHighlighterField("tags"),
		).FragmentSize(150)
		searchService = searchService.Highlight(hl)
	}

	searchResult, err := searchService.Do(ctx)

	if err != nil {
		panic(exceptions.NewBusinessError(utils.SEARCH_EXECUTION_ERROR, err.Error()))
	}

	// 解析结果
	var articles []po.ArticleES
	var articleIDs []int

	for _, hit := range searchResult.Hits.Hits {
		var article po.ArticleES
		if err := json.Unmarshal(hit.Source, &article); err != nil {
			// 处理解析错误
			panic(exceptions.NewBusinessError(utils.SEARCH_RESULT_PARSE_ERROR, err.Error()))
		}
		// 如果有高亮，优先使用高亮内容覆盖字段（带 <em> 标签）
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

		// 记录评分详情
		var score float64
		if hit.Score != nil {
			score = *hit.Score
		}
		utils.Log.Info(fmt.Sprintf(
			utils.SEARCH_METRICS_INFO,
			article.ID, article.Title, article.AIScore, article.UserScore, article.Views, article.LikeCount, article.CollectCount, article.AuthorFollowCount, score,
		))
	}

	// 从数据库获取实际阅读量、点赞数、收藏数、作者关注数替换ES中的数据（ES数据有延迟）
	if len(articleIDs) > 0 {
		articleMapper := &sync.ArticleMapper{}
		likeMapper := &sync.LikeMapper{}
		collectMapper := &sync.CollectMapper{}
		focusMapper := &sync.FocusMapper{}
		viewsMap := articleMapper.GetArticleViewsByIDs(ctx, articleIDs)
		likeCounts := likeMapper.GetLikeCountsByArticleIDs(ctx, articleIDs)
		collectCounts := collectMapper.GetCollectCountsByArticleIDs(ctx, articleIDs)

		// 提取所有作者的UserID
		authorUserIDs := make([]int, 0)
		for _, article := range articles {
			authorUserIDs = append(authorUserIDs, article.UserID)
		}
		// 批量获取作者的关注数（粉丝数）
		authorFollowCounts := focusMapper.GetFollowCountsByUserIDs(ctx, authorUserIDs)

		for i := range articles {
			if views, ok := viewsMap[articles[i].ID]; ok {
				articles[i].Views = views
			}
			if likes, ok := likeCounts[articles[i].ID]; ok {
				articles[i].LikeCount = likes
			}
			if collects, ok := collectCounts[articles[i].ID]; ok {
				articles[i].CollectCount = collects
			}
			if followCount, ok := authorFollowCounts[articles[i].UserID]; ok {
				articles[i].AuthorFollowCount = followCount
			}
		}
	}

	return articles, int(searchResult.Hits.TotalHits.Value)
}

// GetSearchHistory 获取用户搜索历史记录（去重后最近10条）
func (m *SearchMapper) GetSearchHistory(ctx context.Context, userID int64) ([]string, error) {
	// 获取 MongoDB 集合
	collection := config.GetMongoDatabase().Collection("articlelogs")

	// 使用聚合管道实现去重后取前10条
	pipeline := []bson.M{
		// 1. 匹配条件：userId 和 action
		{
			"$match": bson.M{
				"userId": userID,
				"action": "search",
			},
		},
		// 2. 按创建时间倒序排序
		{
			"$sort": bson.M{
				"createdAt": -1,
			},
		},
		// 3. 添加 keyword 字段（从 content.Keyword 提取）
		{
			"$addFields": bson.M{
				"keyword": "$content.Keyword",
			},
		},
		// 4. 过滤掉空关键词
		{
			"$match": bson.M{
				"keyword": bson.M{
					"$exists": true,
					"$nin":    []any{nil, ""},
				},
			},
		},
		// 5. 按关键词分组，保留最新的记录
		{
			"$group": bson.M{
				"_id":       "$keyword",
				"createdAt": bson.M{"$first": "$createdAt"},
			},
		},
		// 6. 再次按创建时间倒序排序
		{
			"$sort": bson.M{
				"createdAt": -1,
			},
		},
		// 7. 限制返回10条
		{
			"$limit": 10,
		},
		// 8. 只返回关键词字段
		{
			"$project": bson.M{
				"_id":       0,
				"keyword":   "$_id",
				"createdAt": 1,
			},
		},
	}

	// 执行聚合查询
	cursor, err := collection.Aggregate(ctx, pipeline)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	// 解析结果
	var keywords []string
	for cursor.Next(ctx) {
		var result struct {
			Keyword   string    `bson:"keyword"`
			CreatedAt time.Time `bson:"createdAt"`
		}
		if err := cursor.Decode(&result); err != nil {
			continue
		}
		keywords = append(keywords, result.Keyword)
	}

	return keywords, nil
}
