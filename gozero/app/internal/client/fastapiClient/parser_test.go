package fastapiClient

import "testing"

// 向量增强：下划线字段（FastAPI 默认序列化命名）解析
func TestParseVectorEnhanceResultReadsSnakeCaseItems(t *testing.T) {
	items, err := ParseVectorEnhanceResult(map[string]any{
		"items": []any{
			map[string]any{
				"article_id":   5445,
				"vector_score": 0.82,
				"reason":       "语义匹配",
				"matched_chunks": []any{
					map[string]any{
						"article_id":  5445,
						"title":       "标题",
						"chunk_index": 2,
						"score":       0.91,
						"content":     "片段内容",
					},
				},
			},
		},
	})
	if err != nil {
		t.Fatalf("解析向量增强结果失败: %v", err)
	}
	if len(items) != 1 {
		t.Fatalf("向量增强条目数 = %d，期望 1", len(items))
	}
	if items[0].ArticleID != 5445 || items[0].VectorScore != 0.82 || items[0].Reason != "语义匹配" {
		t.Fatalf("向量增强条目 = %+v", items[0])
	}
	if len(items[0].MatchedChunks) != 1 {
		t.Fatalf("匹配片段数 = %d，期望 1", len(items[0].MatchedChunks))
	}
	chunk := items[0].MatchedChunks[0]
	if chunk.ArticleID != 5445 || chunk.ChunkIndex != 2 || chunk.Score != 0.91 || chunk.Content != "片段内容" {
		t.Fatalf("匹配片段 = %+v", chunk)
	}
}

// 向量增强：驼峰字段同样要能解析（FastAPI 的 Alias 同时接受两种命名）
func TestParseVectorEnhanceResultReadsCamelCaseItems(t *testing.T) {
	items, err := ParseVectorEnhanceResult(map[string]any{
		"items": []any{
			map[string]any{
				"articleId":   2562,
				"vectorScore": 1.1,
				"reason":      "驼峰命中",
				"matchedChunks": []any{
					map[string]any{"articleId": 2562, "chunkIndex": 3, "score": 0.5},
				},
			},
		},
	})
	if err != nil {
		t.Fatalf("解析驼峰向量增强结果失败: %v", err)
	}
	if len(items) != 1 || items[0].ArticleID != 2562 || items[0].VectorScore != 1.1 {
		t.Fatalf("驼峰向量增强条目 = %+v", items)
	}
	if len(items[0].MatchedChunks) != 1 || items[0].MatchedChunks[0].ChunkIndex != 3 {
		t.Fatalf("驼峰匹配片段 = %+v", items[0].MatchedChunks)
	}
}

// 向量增强：合法空结果是空切片而不是错误
func TestParseVectorEnhanceResultAcceptsEmptyItems(t *testing.T) {
	items, err := ParseVectorEnhanceResult(map[string]any{"items": []any{}})
	if err != nil {
		t.Fatalf("空 items 不应报错: %v", err)
	}
	if items == nil || len(items) != 0 {
		t.Fatalf("空 items 应返回空切片，实际: %#v", items)
	}
}

// 向量增强：结构性字段不符必须报错，交由调用方记录降级日志
func TestParseVectorEnhanceResultRejectsInvalidShape(t *testing.T) {
	cases := []struct {
		name string
		data any
	}{
		{name: "顶层不是对象", data: []any{}},
		{name: "items 字段缺失", data: map[string]any{"other": 1}},
		{name: "items 不是数组", data: map[string]any{"items": map[string]any{}}},
		{name: "元素不是对象", data: map[string]any{"items": []any{"invalid"}}},
		{name: "article_id 缺失", data: map[string]any{"items": []any{map[string]any{"vector_score": 0.5}}}},
		{name: "article_id 非数值", data: map[string]any{"items": []any{map[string]any{"article_id": "5445"}}}},
		{name: "article_id 为 0", data: map[string]any{"items": []any{map[string]any{"article_id": 0}}}},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if _, err := ParseVectorEnhanceResult(c.data); err == nil {
				t.Fatalf("应返回解析错误: %#v", c.data)
			}
		})
	}
}

// 图谱增强：解析文章 ID、得分、关系证据与命中标签路径
func TestParseGraphEnhanceResultReadsRelationsAndTags(t *testing.T) {
	items, err := ParseGraphEnhanceResult(map[string]any{
		"items": []any{
			map[string]any{
				"article_id":  5445,
				"graph_score": 0.63,
				"reason":      "共同作者",
				"relations": []any{
					map[string]any{"type": "AUTHOR", "name": "张三", "score": 0.9, "reason": "共同作者"},
				},
				"matched_tags":  []any{"Go", "微服务"},
				"matched_paths": []any{"文章→作者→文章"},
			},
		},
	})
	if err != nil {
		t.Fatalf("解析图谱增强结果失败: %v", err)
	}
	if len(items) != 1 || items[0].ArticleID != 5445 || items[0].GraphScore != 0.63 {
		t.Fatalf("图谱增强条目 = %+v", items)
	}
	if len(items[0].Relations) != 1 || items[0].Relations[0].Type != "AUTHOR" || items[0].Relations[0].Score != 0.9 {
		t.Fatalf("图谱关系 = %+v", items[0].Relations)
	}
	if len(items[0].MatchedTags) != 2 || items[0].MatchedTags[0] != "Go" {
		t.Fatalf("命中标签 = %+v", items[0].MatchedTags)
	}
	if len(items[0].MatchedPaths) != 1 || items[0].MatchedPaths[0] != "文章→作者→文章" {
		t.Fatalf("命中路径 = %+v", items[0].MatchedPaths)
	}
}

// 图谱增强：结构性字段不符必须报错
func TestParseGraphEnhanceResultRejectsInvalidShape(t *testing.T) {
	cases := []struct {
		name string
		data any
	}{
		{name: "顶层不是对象", data: "invalid"},
		{name: "items 字段缺失", data: map[string]any{}},
		{name: "元素不是对象", data: map[string]any{"items": []any{1}}},
		{name: "article_id 非数值", data: map[string]any{"items": []any{map[string]any{"article_id": true}}}},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if _, err := ParseGraphEnhanceResult(c.data); err == nil {
				t.Fatalf("应返回解析错误: %#v", c.data)
			}
		})
	}
}
