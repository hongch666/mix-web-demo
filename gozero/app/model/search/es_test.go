package search

import (
	"testing"

	"app/common/client"
	"app/common/constants"
	"app/internal/client/springClient"
)

// TestSearchStatsFillMetricsAreUnique 校验回填指标名无重复且覆盖评论评分
// 指标名与检索时的并行拉取顺序一一对应，重复或缺失会导致降级日志错位
func TestSearchStatsFillMetricsAreUnique(t *testing.T) {
	seen := make(map[string]bool, len(constants.SEARCH_STATS_FILL_METRICS))
	for _, metric := range constants.SEARCH_STATS_FILL_METRICS {
		if seen[metric] {
			t.Fatalf("回填指标名重复: %s", metric)
		}
		seen[metric] = true
	}

	if !seen["comment_scores"] {
		t.Fatal("回填指标名缺少 comment_scores")
	}
}

// TestApplyCommentScoresOverwritesSnapshot 校验 AI 与用户评分被 Spring 实时值覆盖
func TestApplyCommentScoresOverwritesSnapshot(t *testing.T) {
	article := ArticleES{ID: 1, AIScore: 1.5, AICommentCount: 1, UserScore: 2.5, UserCommentCount: 2}

	applyCommentScores(&article, map[string]springClient.CommentScoreVO{
		"ai":   {AverageScore: 8.6, Count: 9},
		"user": {AverageScore: 6.1, Count: 3},
	})

	if article.AIScore != 8.6 || article.AICommentCount != 9 {
		t.Fatalf("AI 评分回填结果 = (%v, %d)，期望 (8.6, 9)", article.AIScore, article.AICommentCount)
	}
	if article.UserScore != 6.1 || article.UserCommentCount != 3 {
		t.Fatalf("用户评分回填结果 = (%v, %d)，期望 (6.1, 3)", article.UserScore, article.UserCommentCount)
	}
}

// TestApplyCommentScoresKeepsSnapshotWhenScoresMissing 校验缺失的评分类型保留 ES 文档原值
func TestApplyCommentScoresKeepsSnapshotWhenScoresMissing(t *testing.T) {
	cases := []struct {
		name   string
		scores map[string]springClient.CommentScoreVO
	}{
		{name: "评分为空", scores: nil},
		{name: "只有AI评分", scores: map[string]springClient.CommentScoreVO{"ai": {AverageScore: 7, Count: 2}}},
		{name: "只有用户评分", scores: map[string]springClient.CommentScoreVO{"user": {AverageScore: 7, Count: 2}}},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			article := ArticleES{ID: 1, AIScore: 1.5, AICommentCount: 1, UserScore: 2.5, UserCommentCount: 2}

			applyCommentScores(&article, c.scores)

			if _, ok := c.scores["ai"]; !ok && (article.AIScore != 1.5 || article.AICommentCount != 1) {
				t.Fatalf("AI 评分缺失时应保留 ES 文档原值，实际 = (%v, %d)", article.AIScore, article.AICommentCount)
			}
			if _, ok := c.scores["user"]; !ok && (article.UserScore != 2.5 || article.UserCommentCount != 2) {
				t.Fatalf("用户评分缺失时应保留 ES 文档原值，实际 = (%v, %d)", article.UserScore, article.UserCommentCount)
			}
		})
	}
}

// TestApplyCommentScoresKeepsSnapshotOnParseFailure 校验评分接口降级（无有效数据）时保留 ES 文档原值
func TestApplyCommentScoresKeepsSnapshotOnParseFailure(t *testing.T) {
	scores, err := springClient.ParseCommentScoresMap(client.Result{})
	if err == nil {
		t.Fatal("空响应应返回解析错误")
	}

	article := ArticleES{ID: 1, AIScore: 1.5, AICommentCount: 1, UserScore: 2.5, UserCommentCount: 2}
	applyCommentScores(&article, scores[article.ID])

	if article.AIScore != 1.5 || article.AICommentCount != 1 {
		t.Fatalf("接口降级时 AI 评分应保留原值，实际 = (%v, %d)", article.AIScore, article.AICommentCount)
	}
	if article.UserScore != 2.5 || article.UserCommentCount != 2 {
		t.Fatalf("接口降级时用户评分应保留原值，实际 = (%v, %d)", article.UserScore, article.UserCommentCount)
	}
}

// TestApplyCommentScoresFromSpringResponse 校验 Spring 评分响应可解析并按角色回填到文章
func TestApplyCommentScoresFromSpringResponse(t *testing.T) {
	result := client.Result{Data: map[string]any{
		"1": map[string]any{
			"ai":   map[string]any{"average_score": 8.5, "count": 4},
			"user": map[string]any{"average_score": 6.0, "count": 2},
		},
	}}

	scores, err := springClient.ParseCommentScoresMap(result)
	if err != nil {
		t.Fatal(err)
	}

	article := ArticleES{ID: 1}
	applyCommentScores(&article, scores[article.ID])

	if article.AIScore != 8.5 || article.AICommentCount != 4 {
		t.Fatalf("AI 评分解析回填结果 = (%v, %d)，期望 (8.5, 4)", article.AIScore, article.AICommentCount)
	}
	if article.UserScore != 6.0 || article.UserCommentCount != 2 {
		t.Fatalf("用户评分解析回填结果 = (%v, %d)，期望 (6, 2)", article.UserScore, article.UserCommentCount)
	}
}
