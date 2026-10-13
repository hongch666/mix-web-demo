package springClient

import (
	"testing"

	"app/common/client"
)

// TestParseArticleViewsMapReadsIdCountList 校验阅读量按 Spring 的 [{id, count}] 结构解析
func TestParseArticleViewsMapReadsIdCountList(t *testing.T) {
	result := client.Result{Data: []any{
		map[string]any{"id": 5445, "count": 2401},
		map[string]any{"id": 2562, "count": 93},
	}}

	views, err := ParseArticleViewsMap(result)
	if err != nil {
		t.Fatal(err)
	}

	if views[5445] != 2401 || views[2562] != 93 {
		t.Fatalf("阅读量解析结果 = %v，期望 {5445:2401, 2562:93}", views)
	}
}

// TestParseCountsMapReadsNestedCounts 校验点赞/收藏/粉丝数按 Spring 的 {counts:[{id, count}]} 结构解析
func TestParseCountsMapReadsNestedCounts(t *testing.T) {
	result := client.Result{Data: map[string]any{
		"counts": []any{
			map[string]any{"id": 5445, "count": 7},
			map[string]any{"id": 2562, "count": 0},
		},
	}}

	counts, err := ParseCountsMap(result)
	if err != nil {
		t.Fatal(err)
	}

	if counts[5445] != 7 {
		t.Fatalf("计数解析结果 = %v，期望 5445 对应 7", counts)
	}
	// 零值项要保留：调用方按存在性判断能否覆盖 ES 文档原值
	if _, ok := counts[2562]; !ok {
		t.Fatalf("计数解析结果缺少零值项: %v", counts)
	}
}

// TestParseCommentScoresMapReadsRoleScores 校验评论评分按 Spring 的 [{article_id, role_scores}] 结构解析
func TestParseCommentScoresMapReadsRoleScores(t *testing.T) {
	result := client.Result{Data: []any{
		map[string]any{
			"article_id": 5445,
			"role_scores": map[string]any{
				"ai":   map[string]any{"average_score": 8.6, "count": 9},
				"user": map[string]any{"average_score": 6.1, "count": 3},
			},
		},
	}}

	scores, err := ParseCommentScoresMap(result)
	if err != nil {
		t.Fatal(err)
	}

	articleScores, ok := scores[5445]
	if !ok {
		t.Fatalf("评论评分解析结果缺少文章 5445: %v", scores)
	}
	if articleScores["ai"].AverageScore != 8.6 || articleScores["ai"].Count != 9 {
		t.Fatalf("AI 评分解析结果 = %+v", articleScores["ai"])
	}
	if articleScores["user"].AverageScore != 6.1 || articleScores["user"].Count != 3 {
		t.Fatalf("用户评分解析结果 = %+v", articleScores["user"])
	}
}

// TestParseCountsMapRejectsLegacyMapShape 校验旧的 Map 结构不再被静默接受
// 契约变更后必须返回错误，上层据此记录降级日志并重刷 ES，而不是把 0 当成真实统计
func TestParseCountsMapRejectsLegacyMapShape(t *testing.T) {
	result := client.Result{Data: map[string]any{"5445": 7}}

	if _, err := ParseCountsMap(result); err == nil {
		t.Fatal("旧的 Map 结构应解析失败")
	}
}

// TestParseArticleViewsMapRejectsLegacyMapShape 校验阅读量的旧 Map 结构同样不再被接受
func TestParseArticleViewsMapRejectsLegacyMapShape(t *testing.T) {
	result := client.Result{Data: map[string]any{"5445": 2401}}

	if _, err := ParseArticleViewsMap(result); err == nil {
		t.Fatal("旧的 Map 结构应解析失败")
	}
}
