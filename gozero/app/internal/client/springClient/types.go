package springClient

import (
	"context"
	"encoding/json"
	"fmt"

	"app/common/client"
	"app/common/constants"
)

// Client 定义 GoZero 使用的 Spring 调用契约，便于业务层隔离远程依赖
type Client interface {
	GetPublishedArticles(context.Context, int, int) (client.Result, error)
	GetArticleViewsByIDs(context.Context, []int64) (client.Result, error)
	GetArticlesByIDs(context.Context, []int64) (client.Result, error)
	IsAdminUser(context.Context, int64) (bool, error)
	GetUsersByIDs(context.Context, []int64) (client.Result, error)
	GetCommentScoresByArticleIDs(context.Context, []int64) (client.Result, error)
	GetLikeCountsByArticleIDs(context.Context, []int64) (client.Result, error)
	GetCollectCountsByArticleIDs(context.Context, []int64) (client.Result, error)
	GetFollowCountsByUserIDs(context.Context, []int64) (client.Result, error)
	GetCategoriesByIDs(context.Context, []int64) (client.Result, error)
	GetSubCategoriesByIDs(context.Context, []int64) (client.Result, error)
}

// parseData 从 client.Result 中解析 Data 字段到目标类型
func parseData[T any](result client.Result) (T, error) {
	var zero T
	if result.Data == nil {
		return zero, fmt.Errorf(constants.RESPONSE_DATA_EMPTY)
	}
	jsonBytes, err := json.Marshal(result.Data)
	if err != nil {
		return zero, fmt.Errorf(constants.RESPONSE_DATA_SERIALIZE, err)
	}
	var target T
	if err := json.Unmarshal(jsonBytes, &target); err != nil {
		return zero, fmt.Errorf(constants.RESPONSE_DATA_DESERIALIZE, err)
	}
	return target, nil
}

// ArticleVO 文章视图对象
type ArticleVO struct {
	ID              int64  `json:"id"`
	Title           string `json:"title"`
	Content         string `json:"content"`
	UserID          int64  `json:"user_id"`
	Username        string `json:"username"`
	Tags            string `json:"tags"`
	Status          int    `json:"status"`
	Views           int    `json:"views"`
	SubCategoryID   int    `json:"sub_category_id"`
	SubCategoryName string `json:"sub_category_name"`
	CategoryID      int64  `json:"category_id"`
	CategoryName    string `json:"category_name"`
	CreateAt        string `json:"create_at"`
	UpdateAt        string `json:"update_at"`
}

// UserVO 用户视图对象
type UserVO struct {
	ID    int64  `json:"id"`
	Name  string `json:"name"`
	Role  string `json:"role"`
	Img   string `json:"img"`
	Email string `json:"email"`
}

// CommentScoreVO 评论评分
type CommentScoreVO struct {
	AverageScore float64 `json:"average_score"`
	Count        int64   `json:"count"`
}

// IdCountVO Spring 批量统计返回的元素，字段与 Spring 的 IdCountVO 保持一致
type IdCountVO struct {
	ID    int64 `json:"id"`
	Count int64 `json:"count"`
}

// BatchCountVO Spring 点赞/收藏/粉丝数批量接口的返回体，数量包在 counts 字段里
type BatchCountVO struct {
	Counts []IdCountVO `json:"counts"`
}

// ArticleCommentScoresVO Spring 评论评分返回的元素，按角色分组
type ArticleCommentScoresVO struct {
	ArticleID  int64                     `json:"article_id"`
	RoleScores map[string]CommentScoreVO `json:"role_scores"`
}

// CategoryVO 分类视图对象
type CategoryVO struct {
	ID   int64  `json:"id"`
	Name string `json:"name"`
}

// SubCategoryVO 子分类视图对象
type SubCategoryVO struct {
	ID         int64  `json:"id"`
	Name       string `json:"name"`
	CategoryID int64  `json:"category_id"`
}

// PageVO 分页视图对象
type PageVO[T any] struct {
	Total   int64 `json:"total"`
	Records []T   `json:"list"`
}

// ParseArticleVOs 解析文章列表
func ParseArticleVOs(result client.Result) ([]ArticleVO, error) {
	return parseData[[]ArticleVO](result)
}

// ParseArticlePage 解析分页文章列表
func ParseArticlePage(result client.Result) ([]ArticleVO, int64, error) {
	page, err := parseData[PageVO[ArticleVO]](result)
	if err != nil {
		return nil, 0, err
	}
	return page.Records, page.Total, nil
}

// ParseArticleViewsMap 解析文章阅读量：Spring 返回 [{id, count}]，这里转成 文章ID → 阅读量
func ParseArticleViewsMap(result client.Result) (map[int64]int, error) {
	items, err := parseData[[]IdCountVO](result)
	if err != nil {
		return nil, err
	}

	views := make(map[int64]int, len(items))
	for _, item := range items {
		views[item.ID] = int(item.Count)
	}
	return views, nil
}

// ParseUserVOs 解析用户列表
func ParseUserVOs(result client.Result) ([]UserVO, error) {
	return parseData[[]UserVO](result)
}

// ParseCommentScoresMap 解析评论评分：Spring 返回 [{article_id, role_scores}]，这里转成 文章ID → 角色 → 评分
func ParseCommentScoresMap(result client.Result) (map[int64]map[string]CommentScoreVO, error) {
	items, err := parseData[[]ArticleCommentScoresVO](result)
	if err != nil {
		return nil, err
	}

	scores := make(map[int64]map[string]CommentScoreVO, len(items))
	for _, item := range items {
		scores[item.ArticleID] = item.RoleScores
	}
	return scores, nil
}

// ParseCountsMap 解析计数（点赞/收藏/粉丝数）：Spring 返回 {counts: [{id, count}]}，这里转成 ID → 数量
func ParseCountsMap(result client.Result) (map[int64]int64, error) {
	body, err := parseData[BatchCountVO](result)
	if err != nil {
		return nil, err
	}

	// counts 缺失说明响应结构与契约不符（历史版本直接返回 Map），显式报错让上层记录降级
	// 合法空结果是 "counts": []，反序列化后是非 nil 空切片，与字段缺失可区分
	if body.Counts == nil {
		return nil, fmt.Errorf(constants.RESPONSE_DATA_EMPTY)
	}

	counts := make(map[int64]int64, len(body.Counts))
	for _, item := range body.Counts {
		counts[item.ID] = item.Count
	}
	return counts, nil
}

// ParseCategoryVOs 解析分类列表
func ParseCategoryVOs(result client.Result) ([]CategoryVO, error) {
	return parseData[[]CategoryVO](result)
}

// ParseSubCategoryVOs 解析子分类列表
func ParseSubCategoryVOs(result client.Result) ([]SubCategoryVO, error) {
	return parseData[[]SubCategoryVO](result)
}
