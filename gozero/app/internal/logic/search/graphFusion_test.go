package search

import (
	"testing"

	"app/internal/client/fastapiClient"
	"app/internal/types"
)

// 验证未启用增强时保留ES排序并填充分数字段
func TestFillDefaultScoresKeepsESOrder(t *testing.T) {
	articles := []types.ArticleEsItem{{Id: 1, EsScore: 2}, {Id: 2, EsScore: 1}}
	FillDefaultScores(articles)
	if articles[0].EsScore != 1 || articles[1].FinalScore != 0.5 {
		t.Fatalf("默认分数填充结果不正确: %+v", articles)
	}
}

// 验证融合结果按最终得分降序排列并保留图谱和向量解释
func TestMergeAndRerankSortsAndCarriesReasons(t *testing.T) {
	articles := []types.ArticleEsItem{{Id: 1, EsScore: 1}, {Id: 2, EsScore: 2}}
	result := MergeAndRerank(articles,
		[]fastapiClient.VectorEnhanceItem{{ArticleID: 1, VectorScore: 1, Reason: "语义匹配"}},
		[]fastapiClient.GraphEnhanceItem{{ArticleID: 1, GraphScore: 1, Reason: "图谱关联"}},
		FusionConfig{VectorEnabled: true, GraphEnabled: true, HasKeyword: true, IsLoggedIn: true, VectorScoreWeight: 0.5, GraphScoreWeight: 0.3, HybridMinESWeight: 0.2},
	)
	if result[1].Id != 1 || result[1].Reason != "图谱关联" || result[1].SemanticReason != "语义匹配" || result[0].FinalScore < result[1].FinalScore {
		t.Fatalf("融合排序或解释不正确: %+v", result)
	}
}

// 验证未登录用户不会使用图谱权重
func TestNewFusionEngineDisablesGraphForAnonymousUser(t *testing.T) {
	engine := NewFusionEngine(FusionConfig{VectorEnabled: true, GraphEnabled: true, HasKeyword: true, VectorScoreWeight: 0.4, GraphScoreWeight: 0.4, HybridMinESWeight: 0.2})
	if engine.graphWeight != 0 || engine.vectorWeight < 0.3 {
		t.Fatalf("匿名用户融合权重不正确: %+v", engine)
	}
}
