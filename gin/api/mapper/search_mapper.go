package mapper

import (
	"context"
	"encoding/json"
	"gin_proj/config"
	"gin_proj/entity/dto"
	"gin_proj/entity/po"
	"time"

	"github.com/olivere/elastic"
)

func SearchArticle(ctx context.Context, searchDTO dto.ArticleSearchDTO) ([]po.ArticleES, int) {
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

	// 执行搜索
	esClient := config.ESClient
	searchResult, err := esClient.Search().
		Index("articles").
		Query(boolQuery).
		Sort("views", false).
		Sort("create_at", false). // 按发布时间倒序
		From(from).Size(size).
		Do(ctx)

	if err != nil {
		panic(err.Error())
	}

	// 解析结果
	var articles []po.ArticleES
	for _, hit := range searchResult.Hits.Hits {
		var article po.ArticleES
		if err := json.Unmarshal(hit.Source, &article); err == nil {
			articles = append(articles, article)
		} else {
			// 处理解析错误
			panic(err.Error())
		}
	}

	return articles, int(searchResult.Hits.TotalHits.Value)
}
