package fastapiClient

import (
	"fmt"

	"app/common/constants"
)

// 解析契约：结构性字段（顶层对象、items 数组、元素对象与 article_id）不符时返回错误，
// 由调用方记录降级日志；items 为合法空数组时返回空切片，不算错误
// reason、score、匹配片段等展示字段保持宽松，类型不符时取零值
//
// ParseVectorEnhanceResult 从完整响应 data 字段中解析向量增强结果
func ParseVectorEnhanceResult(data any) ([]VectorEnhanceItem, error) {
	dataMap, ok := data.(map[string]any)
	if !ok {
		return nil, fmt.Errorf(constants.RESPONSE_ITEMS_INVALID)
	}

	itemsRaw, ok := dataMap["items"].([]any)
	if !ok {
		return nil, fmt.Errorf(constants.RESPONSE_ITEMS_INVALID)
	}

	items := make([]VectorEnhanceItem, 0, len(itemsRaw))
	for _, itemRaw := range itemsRaw {
		itemMap, ok := itemRaw.(map[string]any)
		if !ok {
			return nil, fmt.Errorf(constants.RESPONSE_ITEM_INVALID)
		}

		// 文章 ID 是候选与 ES 文档配对的关键字段，缺失或非法会让该条候选静默失效
		articleID, ok := toInt64(getMapValue(itemMap, "article_id", "articleId"))
		if !ok || articleID <= 0 {
			return nil, fmt.Errorf(constants.RESPONSE_ARTICLE_ID_INVALID)
		}

		vectorScore, _ := toFloat64(getMapValue(itemMap, "vector_score", "vectorScore"))
		reason, _ := toString(itemMap["reason"])

		items = append(items, VectorEnhanceItem{
			ArticleID:     articleID,
			VectorScore:   vectorScore,
			Reason:        reason,
			MatchedChunks: parseVectorMatchedChunks(getMapValue(itemMap, "matched_chunks", "matchedChunks")),
		})
	}

	return items, nil
}

// ParseGraphEnhanceResult 从完整响应 data 字段中解析图谱增强结果
func ParseGraphEnhanceResult(data any) ([]GraphEnhanceItem, error) {
	dataMap, ok := data.(map[string]any)
	if !ok {
		return nil, fmt.Errorf(constants.RESPONSE_ITEMS_INVALID)
	}

	itemsRaw, ok := dataMap["items"].([]any)
	if !ok {
		return nil, fmt.Errorf(constants.RESPONSE_ITEMS_INVALID)
	}

	items := make([]GraphEnhanceItem, 0, len(itemsRaw))
	for _, itemRaw := range itemsRaw {
		itemMap, ok := itemRaw.(map[string]any)
		if !ok {
			return nil, fmt.Errorf(constants.RESPONSE_ITEM_INVALID)
		}

		articleID, ok := toInt64(getMapValue(itemMap, "article_id", "articleId"))
		if !ok || articleID <= 0 {
			return nil, fmt.Errorf(constants.RESPONSE_ARTICLE_ID_INVALID)
		}

		graphScore, _ := toFloat64(getMapValue(itemMap, "graph_score", "graphScore"))
		reason, _ := toString(itemMap["reason"])

		items = append(items, GraphEnhanceItem{
			ArticleID:    articleID,
			GraphScore:   graphScore,
			Reason:       reason,
			Relations:    parseRelations(itemMap["relations"]),
			MatchedTags:  parseStringSlice(getMapValue(itemMap, "matched_tags", "matchedTags")),
			MatchedPaths: parseStringSlice(getMapValue(itemMap, "matched_paths", "matchedPaths")),
		})
	}

	return items, nil
}

// 类型转换辅助函数
func getMapValue(m map[string]any, keys ...string) any {
	for _, key := range keys {
		if value, ok := m[key]; ok {
			return value
		}
	}
	return nil
}

// toInt64 将任意值宽松转换为 int64，仅接受 float64、int64、int，其他类型返回失败
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

// toFloat64 将任意值宽松转换为 float64，仅接受 float64、int、int64，其他类型返回失败
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

// toString 将任意值断言为字符串，类型不符时返回失败
func toString(v any) (string, bool) {
	s, ok := v.(string)
	return s, ok
}

// parseRelations 解析图谱增强结果中的关系列表，元素不合法时跳过
func parseRelations(v any) []GraphRelation {
	rawList, ok := v.([]any)
	if !ok {
		return []GraphRelation{}
	}

	relations := make([]GraphRelation, 0, len(rawList))
	for _, raw := range rawList {
		m, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		relType, _ := toString(m["type"])
		name, _ := toString(m["name"])
		score, _ := toFloat64(m["score"])
		reason, _ := toString(m["reason"])
		relations = append(relations, GraphRelation{
			Type:   relType,
			Name:   name,
			Score:  score,
			Reason: reason,
		})
	}
	return relations
}

// parseStringSlice 将任意值解析为字符串切片，非字符串元素被忽略
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

// parseVectorMatchedChunks 解析向量增强结果中的匹配片段列表，元素不合法时跳过
func parseVectorMatchedChunks(v any) []VectorMatchedChunk {
	rawList, ok := v.([]any)
	if !ok {
		return []VectorMatchedChunk{}
	}

	chunks := make([]VectorMatchedChunk, 0, len(rawList))
	for _, raw := range rawList {
		m, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		articleID, _ := toInt64(getMapValue(m, "article_id", "articleId"))
		title, _ := toString(m["title"])
		chunkIndex64, _ := toInt64(getMapValue(m, "chunk_index", "chunkIndex"))
		score, _ := toFloat64(m["score"])
		content, _ := toString(m["content"])
		chunks = append(chunks, VectorMatchedChunk{
			ArticleID:  articleID,
			Title:      title,
			ChunkIndex: int(chunkIndex64),
			Score:      score,
			Content:    content,
		})
	}
	return chunks
}
