package springClient

import (
	"encoding/json"
	"fmt"

	"app/common/client"
	"app/common/constants"
)

// 解析入口统一走 parseData：Data 为空、序列化失败或结构与契约不符时都返回错误，
// 由调用方记录降级日志，不要静默吞掉解析错误

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
