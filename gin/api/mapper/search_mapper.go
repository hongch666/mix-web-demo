package mapper

import (
	"context"
	"encoding/json"
	"fmt"
	"gin_proj/common/client"
	"gin_proj/config"
	"gin_proj/entity/dto"
	"gin_proj/entity/po"
	"net/http"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
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

func SearchArticles(c *gin.Context) []po.Article {
	// 调用Spring部分接口获取文章数据
	opts := client.RequestOptions{
		Method: http.MethodGet,
	}
	sd := client.NewServiceDiscovery(config.NamingClient)
	result, err := sd.CallService(c, "spring", "/articles/list", opts)
	if err != nil {
		panic(err.Error())
	}

	// 解析result.Data中的文章列表
	var articles []po.Article
	var data struct {
		Total int          `json:"total"`
		List  []po.Article `json:"list"`
	}
	dataBytes, _ := json.Marshal(result.Data)
	if err := json.Unmarshal(dataBytes, &data); err != nil {
		panic(err.Error())
	}
	articles = data.List

	return articles
}

func SearchUserByIds(c *gin.Context, userIDs []int) []po.User {
	// 将[]int转换为逗号分隔的字符串
	idStrings := make([]string, len(userIDs))
	for i, id := range userIDs {
		idStrings[i] = fmt.Sprintf("%d", id)
	}
	idsParam := strings.Join(idStrings, ",")

	opts := client.RequestOptions{
		Method: http.MethodGet,
		PathParams: map[string]string{
			"ids": idsParam,
		},
	}
	sd := client.NewServiceDiscovery(config.NamingClient)
	result, err := sd.CallService(c, "spring", "/users/batch/:ids", opts)
	if err != nil {
		panic(err.Error())
	}

	// 解析result.Data中的用户列表
	var users []po.User
	var data struct {
		Total int       `json:"total"`
		List  []po.User `json:"list"`
	}
	dataBytes, _ := json.Marshal(result.Data)
	if err := json.Unmarshal(dataBytes, &data); err != nil {
		// 如果直接解析失败，尝试解析为数组
		if err := json.Unmarshal(dataBytes, &users); err != nil {
			panic(fmt.Sprintf("用户数据解析失败: %v, 数据: %s", err, string(dataBytes)))
		}
	} else {
		users = data.List
	}

	return users
}

func SearchSubCategoriesByIds(c *gin.Context, subCategoryIDs []int) []po.SubCategory {
	// 将[]int转换为逗号分隔的字符串
	idStrings := make([]string, len(subCategoryIDs))
	for i, id := range subCategoryIDs {
		idStrings[i] = fmt.Sprintf("%d", id)
	}
	idsParam := strings.Join(idStrings, ",")

	opts := client.RequestOptions{
		Method: http.MethodGet,
		PathParams: map[string]string{
			"ids": idsParam,
		},
	}
	sd := client.NewServiceDiscovery(config.NamingClient)
	result, err := sd.CallService(c, "spring", "/category/sub/batch/:ids", opts)
	if err != nil {
		panic(err.Error())
	}

	// 解析result.Data中的子分类列表
	var subCategories []po.SubCategory
	var data struct {
		Total int              `json:"total"`
		List  []po.SubCategory `json:"list"`
	}
	dataBytes, _ := json.Marshal(result.Data)
	if err := json.Unmarshal(dataBytes, &data); err != nil {
		// 如果解析为包含total和list的结构失败，尝试直接解析为数组
		if err := json.Unmarshal(dataBytes, &subCategories); err != nil {
			panic(err.Error())
		}
	} else {
		subCategories = data.List
	}
	return subCategories
}

func SearchCategoriesByIds(c *gin.Context, categoryIDs []int) []po.Category {
	// 将[]int转换为逗号分隔的字符串
	idStrings := make([]string, len(categoryIDs))
	for i, id := range categoryIDs {
		idStrings[i] = fmt.Sprintf("%d", id)
	}
	idsParam := strings.Join(idStrings, ",")

	opts := client.RequestOptions{
		Method: http.MethodGet,
		PathParams: map[string]string{
			"ids": idsParam,
		},
	}
	sd := client.NewServiceDiscovery(config.NamingClient)
	result, err := sd.CallService(c, "spring", "/category/batch/:ids", opts)
	if err != nil {
		panic(err.Error())
	}

	// 解析result.Data中的分类列表
	var categories []po.Category
	var data struct {
		Total int           `json:"total"`
		List  []po.Category `json:"list"`
	}
	dataBytes, _ := json.Marshal(result.Data)
	if err := json.Unmarshal(dataBytes, &data); err != nil {
		// 如果解析为包含total和list的结构失败，尝试直接解析为数组
		if err := json.Unmarshal(dataBytes, &categories); err != nil {
			panic(err.Error())
		}
	} else {
		categories = data.List
	}
	return categories
}
