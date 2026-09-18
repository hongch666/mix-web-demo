package search

import (
	"strings"

	"app/internal/types"
)

// normalizeSearchMode 规范化搜索模式，缺省或仅空白时取 hybrid
func normalizeSearchMode(req *types.SearchArticlesReq) string {
	if req.Mode == nil || strings.TrimSpace(*req.Mode) == "" {
		return "hybrid"
	}
	return strings.ToLower(strings.TrimSpace(*req.Mode))
}

// isVectorEnhanceEnabled 判断本次搜索是否启用向量增强
// keyword 模式下没有语义检索需求，未提供关键词时也无需计算语义相似度
func isVectorEnhanceEnabled(req *types.SearchArticlesReq, keyword string) bool {
	if normalizeSearchMode(req) == "keyword" || strings.TrimSpace(keyword) == "" {
		return false
	}
	if req.EnableVector != nil {
		return *req.EnableVector
	}
	return true
}

// isGraphEnhanceEnabled 判断本次搜索是否启用图谱增强
// 与向量增强不同，图谱按文章关系扩召回，不依赖关键词
func isGraphEnhanceEnabled(req *types.SearchArticlesReq) bool {
	if normalizeSearchMode(req) == "keyword" {
		return false
	}
	if req.EnableGraph != nil {
		return *req.EnableGraph
	}
	return true
}

// isExplainEnabled 判断是否返回搜索解释字段
func isExplainEnabled(req *types.SearchArticlesReq) bool {
	if req.Explain != nil {
		return *req.Explain
	}
	return true
}
