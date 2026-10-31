package springClient

import (
	"encoding/json"
	"fmt"

	"app/common/client"
	"app/common/constants"
)

// 解析入口统一走 parseData：Data 为空、序列化失败或结构与契约不符时都返回错误，由调用方记录降级日志，不要静默吞掉解析错误

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

// ParseUserVOs 解析用户列表
func ParseUserVOs(result client.Result) ([]UserVO, error) {
	return parseData[[]UserVO](result)
}

// ArticleStats 合并统计结果，已按文章ID与作者用户ID建好映射
type ArticleStats struct {
	Views         map[int64]int
	Likes         map[int64]int64
	Collects      map[int64]int64
	Follows       map[int64]int64
	CommentScores map[int64]map[string]CommentScoreVO
}

// ParseArticleStats 解析合并统计接口的返回体，任一字段缺失视为契约不符
func ParseArticleStats(result client.Result) (ArticleStats, error) {
	var zero ArticleStats
	body, err := parseData[ArticleStatsBatchVO](result)
	if err != nil {
		return zero, err
	}

	// 合法空结果是空数组（反序列化后非 nil），字段缺失说明响应结构与契约不符，需显式报错让上层记录降级
	if body.Views == nil || body.Likes == nil || body.Collects == nil ||
		body.Follows == nil || body.CommentScores == nil {
		return zero, fmt.Errorf(constants.RESPONSE_DATA_EMPTY)
	}

	stats := ArticleStats{
		Views:         make(map[int64]int, len(body.Views)),
		Likes:         make(map[int64]int64, len(body.Likes)),
		Collects:      make(map[int64]int64, len(body.Collects)),
		Follows:       make(map[int64]int64, len(body.Follows)),
		CommentScores: make(map[int64]map[string]CommentScoreVO, len(body.CommentScores)),
	}
	for _, item := range body.Views {
		stats.Views[item.ID] = int(item.Count)
	}
	for _, item := range body.Likes {
		stats.Likes[item.ID] = item.Count
	}
	for _, item := range body.Collects {
		stats.Collects[item.ID] = item.Count
	}
	for _, item := range body.Follows {
		stats.Follows[item.ID] = item.Count
	}
	for _, item := range body.CommentScores {
		stats.CommentScores[item.ArticleID] = item.RoleScores
	}
	return stats, nil
}

// ParseCategoryVOs 解析分类列表
func ParseCategoryVOs(result client.Result) ([]CategoryVO, error) {
	return parseData[[]CategoryVO](result)
}

// ParseSubCategoryVOs 解析子分类列表
func ParseSubCategoryVOs(result client.Result) ([]SubCategoryVO, error) {
	return parseData[[]SubCategoryVO](result)
}
