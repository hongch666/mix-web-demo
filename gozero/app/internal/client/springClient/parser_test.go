package springClient

import (
	"testing"

	"app/common/client"
)

// TestParseArticleStatsReadsAllSections 校验合并统计响应中的五类指标都能解析成按 ID 索引的映射
func TestParseArticleStatsReadsAllSections(t *testing.T) {
	result := client.Result{Data: map[string]any{
		"views":    []any{map[string]any{"id": 5445, "count": 2401}},
		"likes":    []any{map[string]any{"id": 5445, "count": 7}},
		"collects": []any{map[string]any{"id": 5445, "count": 3}},
		"follows":  []any{map[string]any{"id": 88, "count": 12}},
		"comment_scores": []any{map[string]any{
			"article_id": 5445,
			"role_scores": map[string]any{
				"ai":   map[string]any{"average_score": 8.6, "count": 9},
				"user": map[string]any{"average_score": 6.1, "count": 3},
			},
		}},
	}}

	stats, err := ParseArticleStats(result)
	if err != nil {
		t.Fatal(err)
	}

	if stats.Views[5445] != 2401 || stats.Likes[5445] != 7 || stats.Collects[5445] != 3 {
		t.Fatalf("文章指标解析结果 = views:%d likes:%d collects:%d",
			stats.Views[5445], stats.Likes[5445], stats.Collects[5445])
	}
	if stats.Follows[88] != 12 {
		t.Fatalf("粉丝数解析结果 = %d，期望 12", stats.Follows[88])
	}
	scores := stats.CommentScores[5445]
	if scores["ai"].AverageScore != 8.6 || scores["ai"].Count != 9 {
		t.Fatalf("AI 评分解析结果 = %+v", scores["ai"])
	}
	if scores["user"].AverageScore != 6.1 || scores["user"].Count != 3 {
		t.Fatalf("用户评分解析结果 = %+v", scores["user"])
	}
}

// TestParseArticleStatsKeepsZeroValueItems 校验零值项要保留，调用方按存在性判断能否覆盖 ES 文档原值
func TestParseArticleStatsKeepsZeroValueItems(t *testing.T) {
	result := client.Result{Data: map[string]any{
		"views":          []any{map[string]any{"id": 1, "count": 0}},
		"likes":          []any{map[string]any{"id": 1, "count": 0}},
		"collects":       []any{},
		"follows":        []any{},
		"comment_scores": []any{},
	}}

	stats, err := ParseArticleStats(result)
	if err != nil {
		t.Fatal(err)
	}

	if _, ok := stats.Views[1]; !ok {
		t.Fatal("零值阅读量应保留")
	}
	if stats.Collects[1] != 0 {
		t.Fatalf("缺失的收藏应保持零值，实际 = %d", stats.Collects[1])
	}
}

// TestParseArticleStatsRejectsMissingSections 校验任一字段缺失视为契约不符，必须返回错误由上层降级并记录日志
func TestParseArticleStatsRejectsMissingSections(t *testing.T) {
	result := client.Result{Data: map[string]any{
		"views":          []any{},
		"likes":          []any{},
		"collects":       []any{},
		"comment_scores": []any{},
	}}

	if _, err := ParseArticleStats(result); err == nil {
		t.Fatal("缺少 follows 字段时应解析失败")
	}
}

// TestParseArticleStatsRejectsLegacyMapShape 校验旧的 Map 结构不再被静默接受，契约变更后必须返回错误
func TestParseArticleStatsRejectsLegacyMapShape(t *testing.T) {
	result := client.Result{Data: map[string]any{"5445": 7}}

	if _, err := ParseArticleStats(result); err == nil {
		t.Fatal("旧的 Map 结构应解析失败")
	}
}
