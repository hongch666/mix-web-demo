package nestjsClient

// ParseSearchHistoryResult 从完整响应 data 字段中解析搜索历史关键词列表
func ParseSearchHistoryResult(data any) []string {
	dataMap, ok := data.(map[string]any)
	if !ok {
		return []string{}
	}

	keywordsRaw, ok := dataMap["keywords"].([]any)
	if !ok {
		return []string{}
	}

	keywords := make([]string, 0, len(keywordsRaw))
	for _, itemRaw := range keywordsRaw {
		if keyword, ok := itemRaw.(string); ok {
			keywords = append(keywords, keyword)
		}
	}

	return keywords
}
