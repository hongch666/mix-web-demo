package search

import (
	"strings"

	"app/internal/cache"
	"app/internal/client/fastapiClient"
)

// ESQueryParams ES 查询参数
type ESQueryParams struct {
	// 传统8项权重
	EsWeight, AiWeight, UserWeight         float64
	ViewsWeight, LikesWeight               float64
	CollectsWeight, FollowWeight           float64
	RecencyWeight                          float64
	MaxViewsNorm, MaxLikesNorm             float64
	MaxCollectsNorm, MaxFollowsNorm        float64
	DecayDaysSq                            float64

	// 向量
	VectorWeight float64
	QueryVector  []float64

	// 图谱4路权重
	GraphInterestWeight, GraphFollowWeight   float64
	GraphSubcatWeight, GraphKeywordWeight    float64

	// 图谱特征数组
	UserTagList        []string
	FollowedAuthorIds  []int64
	PreferredSubCatIds []int64
	KeywordTags        []string
}

// buildESQueryParams 构建 ES 查询参数（含动态权重裁剪）
func buildESQueryParams(
	keyword string,
	weights fastapiClient.SearchWeights,
	queryVector []float64,
	uf *cache.UserGraphFeatures,
	mode string,
	isLoggedIn bool,
) *ESQueryParams {
	hasKeyword := keyword != ""
	hasVector := len(queryVector) > 0
	hasGraphUser := uf != nil && !uf.IsEmpty()

	// ── 向量权重 ──
	vectorWeight := 0.0
	if mode != "keyword" && hasKeyword && hasVector {
		vectorWeight = weights.VectorScoreWeight
	}

	// ── 图谱4路权重 ──
	graphInterestWeight := 0.0
	graphFollowWeight := 0.0
	graphSubcatWeight := 0.0
	graphKeywordWeight := 0.0

	if mode != "keyword" {
		if hasGraphUser && isLoggedIn {
			graphInterestWeight = weights.GraphInterestWeight
			graphFollowWeight = weights.GraphFollowWeight
			graphSubcatWeight = weights.GraphSubcatWeight
		}
		if hasKeyword {
			graphKeywordWeight = weights.GraphKeywordWeight
		}
	}

	// ── 未登录: 图谱归零，向量提权 ──
	if !isLoggedIn {
		graphInterestWeight = 0
		graphFollowWeight = 0
		graphSubcatWeight = 0
		if hasKeyword && hasVector {
			vectorWeight = max(vectorWeight, 0.30)
		}
	}

	// ── 已登录但空搜索词: 向量归零，图谱提权 ──
	if isLoggedIn && !hasKeyword {
		vectorWeight = 0
		graphKeywordWeight = 0
		if hasGraphUser {
			graphInterestWeight = max(graphInterestWeight, 0.20)
			graphFollowWeight = max(graphFollowWeight, 0.15)
			graphSubcatWeight = max(graphSubcatWeight, 0.12)
		}
	}

	p := &ESQueryParams{
		EsWeight:       weights.ESEWeight,
		AiWeight:       weights.AIRatingWeight,
		UserWeight:     weights.UserRatingWeight,
		ViewsWeight:    weights.ViewsWeight,
		LikesWeight:    weights.LikesWeight,
		CollectsWeight: weights.CollectsWeight,
		FollowWeight:   weights.AuthorFollowWeight,
		RecencyWeight:  weights.RecencyWeight,

		MaxViewsNorm:    weights.MaxViewsNorm,
		MaxLikesNorm:    weights.MaxLikesNorm,
		MaxCollectsNorm: weights.MaxCollectsNorm,
		MaxFollowsNorm:  weights.MaxFollowsNorm,
		DecayDaysSq:     weights.RecencyDecayDays * weights.RecencyDecayDays,

		VectorWeight: vectorWeight,
		QueryVector:  queryVector,

		GraphInterestWeight: graphInterestWeight,
		GraphFollowWeight:   graphFollowWeight,
		GraphSubcatWeight:   graphSubcatWeight,
		GraphKeywordWeight:  graphKeywordWeight,
	}

	// 图谱特征数组（仅有权重不为零时才传）
	if graphInterestWeight > 0 || graphFollowWeight > 0 || graphSubcatWeight > 0 {
		p.UserTagList = uf.TagList
		p.FollowedAuthorIds = uf.FollowedAuthorIds
		p.PreferredSubCatIds = uf.PreferredSubCatIds
	}

	if graphKeywordWeight > 0 {
		p.KeywordTags = splitKeywordToTags(keyword)
	}

	return p
}

func max(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}

func splitKeywordToTags(keyword string) []string {
	if keyword == "" {
		return nil
	}
	var tags []string
	for _, part := range strings.Fields(keyword) {
		part = strings.TrimSpace(part)
		if len(part) >= 2 {
			tags = append(tags, part)
		}
	}
	return tags
}
