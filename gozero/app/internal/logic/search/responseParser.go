package search

import (
	"app/internal/client/fastapiClient"
)

// parseVectorEnhanceResult 从完整响应中解析向量增强结果
func parseVectorEnhanceResult(data any) ([]fastapiClient.VectorEnhanceItem, error) {
	dataMap, ok := data.(map[string]any)
	if !ok {
		return []fastapiClient.VectorEnhanceItem{}, nil
	}

	itemsRaw, ok := dataMap["items"].([]any)
	if !ok {
		return []fastapiClient.VectorEnhanceItem{}, nil
	}

	items := make([]fastapiClient.VectorEnhanceItem, 0, len(itemsRaw))
	for _, itemRaw := range itemsRaw {
		itemMap, ok := itemRaw.(map[string]any)
		if !ok {
			continue
		}

		articleID, _ := toInt64(itemMap["articleId"])
		vectorScore, _ := toFloat64(itemMap["vectorScore"])
		reason, _ := toString(itemMap["reason"])

		items = append(items, fastapiClient.VectorEnhanceItem{
			ArticleID:     articleID,
			VectorScore:   vectorScore,
			Reason:        reason,
			MatchedChunks: parseVectorMatchedChunks(itemMap["matchedChunks"]),
		})
	}

	return items, nil
}

// parseGraphEnhanceResult 从完整响应中解析图谱增强结果
func parseGraphEnhanceResult(data any) ([]fastapiClient.GraphEnhanceItem, error) {
	dataMap, ok := data.(map[string]any)
	if !ok {
		return []fastapiClient.GraphEnhanceItem{}, nil
	}

	itemsRaw, ok := dataMap["items"].([]any)
	if !ok {
		return []fastapiClient.GraphEnhanceItem{}, nil
	}

	items := make([]fastapiClient.GraphEnhanceItem, 0, len(itemsRaw))
	for _, itemRaw := range itemsRaw {
		itemMap, ok := itemRaw.(map[string]any)
		if !ok {
			continue
		}

		articleID, _ := toInt64(itemMap["articleId"])
		graphScore, _ := toFloat64(itemMap["graphScore"])
		reason, _ := toString(itemMap["reason"])

		relations := parseRelations(itemMap["relations"])
		matchedTags := parseStringSlice(itemMap["matchedTags"])
		matchedPaths := parseStringSlice(itemMap["matchedPaths"])

		items = append(items, fastapiClient.GraphEnhanceItem{
			ArticleID:    articleID,
			GraphScore:   graphScore,
			Reason:       reason,
			Relations:    relations,
			MatchedTags:  matchedTags,
			MatchedPaths: matchedPaths,
		})
	}

	return items, nil
}

// 类型转换辅助函数
func toInt64(v any) (int64, bool) {
	switch val := v.(type) {
	case float64:
		return int64(val), true
	case int64:
		return val, true
	case int:
		return int64(val), true
	default:
		return 0, false
	}
}

func toFloat64(v any) (float64, bool) {
	switch val := v.(type) {
	case float64:
		return val, true
	case int:
		return float64(val), true
	case int64:
		return float64(val), true
	default:
		return 0, false
	}
}

func toString(v any) (string, bool) {
	s, ok := v.(string)
	return s, ok
}

func parseRelations(v any) []fastapiClient.GraphRelation {
	rawList, ok := v.([]any)
	if !ok {
		return []fastapiClient.GraphRelation{}
	}

	relations := make([]fastapiClient.GraphRelation, 0, len(rawList))
	for _, raw := range rawList {
		m, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		relType, _ := toString(m["type"])
		name, _ := toString(m["name"])
		score, _ := toFloat64(m["score"])
		reason, _ := toString(m["reason"])
		relations = append(relations, fastapiClient.GraphRelation{
			Type:   relType,
			Name:   name,
			Score:  score,
			Reason: reason,
		})
	}
	return relations
}

func parseStringSlice(v any) []string {
	rawList, ok := v.([]any)
	if !ok {
		return nil
	}
	result := make([]string, 0, len(rawList))
	for _, item := range rawList {
		if s, ok := item.(string); ok {
			result = append(result, s)
		}
	}
	return result
}

func parseVectorMatchedChunks(v any) []fastapiClient.VectorMatchedChunk {
	rawList, ok := v.([]any)
	if !ok {
		return []fastapiClient.VectorMatchedChunk{}
	}

	chunks := make([]fastapiClient.VectorMatchedChunk, 0, len(rawList))
	for _, raw := range rawList {
		m, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		articleID, _ := toInt64(m["articleId"])
		title, _ := toString(m["title"])
		chunkIndex64, _ := toInt64(m["chunkIndex"])
		score, _ := toFloat64(m["score"])
		content, _ := toString(m["content"])
		chunks = append(chunks, fastapiClient.VectorMatchedChunk{
			ArticleID:  articleID,
			Title:      title,
			ChunkIndex: int(chunkIndex64),
			Score:      score,
			Content:    content,
		})
	}
	return chunks
}
