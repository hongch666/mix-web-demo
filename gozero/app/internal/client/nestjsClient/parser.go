package nestjsClient

import (
	"fmt"

	"app/common/constants"
)

// ParseSearchHistoryResult 从完整响应 data 字段中解析搜索历史关键词列表，结构性字段（顶层对象、keywords 数组与元素类型）不符时返回错误，由调用方记录日志后降级为空列表；keywords 为合法空数组时返回空切片，不算错误
func ParseSearchHistoryResult(data any) ([]string, error) {
	dataMap, ok := data.(map[string]any)
	if !ok {
		return nil, fmt.Errorf(constants.RESPONSE_KEYWORDS_INVALID)
	}

	keywordsRaw, ok := dataMap["keywords"].([]any)
	if !ok {
		return nil, fmt.Errorf(constants.RESPONSE_KEYWORDS_INVALID)
	}

	keywords := make([]string, 0, len(keywordsRaw))
	for _, itemRaw := range keywordsRaw {
		keyword, ok := itemRaw.(string)
		if !ok {
			return nil, fmt.Errorf(constants.RESPONSE_KEYWORD_INVALID)
		}
		keywords = append(keywords, keyword)
	}

	return keywords, nil
}
