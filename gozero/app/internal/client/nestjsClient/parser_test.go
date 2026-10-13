package nestjsClient

import "testing"

// 搜索历史正常响应：keywords 列表按顺序解析
func TestParseSearchHistoryResultReadsKeywords(t *testing.T) {
	keywords, err := ParseSearchHistoryResult(map[string]any{
		"keywords": []any{"Go", "微服务", "Elasticsearch"},
	})
	if err != nil {
		t.Fatalf("解析搜索历史失败: %v", err)
	}
	if len(keywords) != 3 || keywords[0] != "Go" || keywords[1] != "微服务" || keywords[2] != "Elasticsearch" {
		t.Fatalf("搜索历史解析结果 = %#v", keywords)
	}
}

// 用户没有搜索历史时是合法空结果，返回空切片而不是错误
func TestParseSearchHistoryResultAcceptsEmptyKeywords(t *testing.T) {
	keywords, err := ParseSearchHistoryResult(map[string]any{"keywords": []any{}})
	if err != nil {
		t.Fatalf("空 keywords 不应报错: %v", err)
	}
	if keywords == nil || len(keywords) != 0 {
		t.Fatalf("空 keywords 应返回空切片，实际: %#v", keywords)
	}
}

// 结构性字段不符必须报错，由调用方记录日志后按空历史降级
func TestParseSearchHistoryResultRejectsInvalidShape(t *testing.T) {
	cases := []struct {
		name string
		data any
	}{
		{name: "顶层不是对象", data: []any{}},
		{name: "keywords 字段缺失", data: map[string]any{"other": 1}},
		{name: "keywords 不是数组", data: map[string]any{"keywords": "Go"}},
		{name: "keywords 元素不是字符串", data: map[string]any{"keywords": []any{"Go", 2}}},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if _, err := ParseSearchHistoryResult(c.data); err == nil {
				t.Fatalf("应返回解析错误: %#v", c.data)
			}
		})
	}
}
