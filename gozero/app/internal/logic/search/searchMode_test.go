package search

import (
	"testing"

	"app/internal/types"
)

func TestSearchEnhancementOptions(t *testing.T) {
	keywordMode := " keyword "
	graphMode := "graph"
	disabled := false
	keyword := "文章"

	if got := normalizeSearchMode(&types.SearchArticlesReq{}); got != "hybrid" {
		t.Errorf("默认搜索模式 = %q, 期望 hybrid", got)
	}
	if isVectorEnhanceEnabled(&types.SearchArticlesReq{Mode: &keywordMode}, keyword) {
		t.Error("keyword 模式不应该启用向量增强")
	}
	if !isVectorEnhanceEnabled(&types.SearchArticlesReq{Mode: &graphMode}, keyword) {
		t.Error("graph 模式默认应该启用向量增强")
	}
	if isGraphEnhanceEnabled(&types.SearchArticlesReq{EnableGraph: &disabled}) {
		t.Error("显式关闭时不应该启用图谱增强")
	}
	if !isExplainEnabled(&types.SearchArticlesReq{}) {
		t.Error("默认应该返回搜索解释")
	}
}
