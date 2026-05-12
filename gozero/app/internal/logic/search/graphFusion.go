package search

import (
	"sort"

	"app/internal/client"
	"app/internal/types"
)

// 融合重排后的文章项
type fusionItem struct {
	esScore     float64
	graphScore  float64
	finalScore  float64
	reason      string
	relations   []client.GraphRelation
}

type FusionConfig struct {
	GraphScoreWeight float64
	HybridMinESWeight float64
	IsLoggedIn       bool
	HasKeyword       bool
}

// FusionEngine 融合打分配置
type FusionEngine struct {
	esWeight  float64
	graphWeight float64
}

// NewFusionEngine 创建融合引擎
func NewFusionEngine(cfg FusionConfig) *FusionEngine {
	esWeight := 1.0 - cfg.GraphScoreWeight
	if cfg.GraphScoreWeight <= 0 {
		esWeight = 1.0
	}

	// 根据用户状态调整权重
	if !cfg.IsLoggedIn {
		esWeight = 0.90
	} else if !cfg.HasKeyword {
		esWeight = 0.30
	}

	// 确保 ES 权重不低于最小值
	if esWeight < cfg.HybridMinESWeight {
		esWeight = cfg.HybridMinESWeight
	}

	graphWeight := 1.0 - esWeight
	if graphWeight < 0 {
		graphWeight = 0
	}

	return &FusionEngine{
		esWeight:     esWeight,
		graphWeight:  graphWeight,
	}
}

// MergeAndRerank 融合 ES 结果和图谱结果并重排
// 只对当前页候选进行重排，不改变 total
func MergeAndRerank(
	articles []types.ArticleEsItem,
	graphItems []client.GraphEnhanceItem,
	cfg FusionConfig,
) []types.ArticleEsItem {
	if len(graphItems) == 0 {
		// 没有图谱结果，按 ES 原有分数返回
		return articles
	}

	// 构建 articleId -> graphItem 的映射
	graphMap := make(map[int64]*client.GraphEnhanceItem, len(graphItems))
	for i := range graphItems {
		item := &graphItems[i]
		graphMap[item.ArticleID] = item
	}

	// 计算当前候选集的最大 ES Score 用于归一化
	maxEsScore := 0.0
	for _, article := range articles {
		if article.EsScore > maxEsScore {
			maxEsScore = article.EsScore
		}
	}

	engine := NewFusionEngine(cfg)

	// 为每篇文章计算最终分
	for i := range articles {
		article := &articles[i]
		normalizedEsScore := 0.0
		if maxEsScore > 0 {
			normalizedEsScore = article.EsScore / maxEsScore
		}

		graphScore := 0.0
		reason := ""
		relations := make([]types.GraphRelation, 0)

		if gItem, ok := graphMap[article.Id]; ok {
			graphScore = gItem.GraphScore
			if graphScore < 0 {
				graphScore = 0
			}
			if graphScore > 1 {
				graphScore = 1
			}
			reason = gItem.Reason

			// 转换 relations
			for _, r := range gItem.Relations {
				relations = append(relations, types.GraphRelation{
					Type:   r.Type,
					Name:   r.Name,
					Score:  r.Score,
					Reason: r.Reason,
				})
			}
		}

		finalScore := normalizedEsScore*engine.esWeight + graphScore*engine.graphWeight

		article.EsScore = roundTo4(normalizedEsScore)
		article.GraphScore = roundTo4(graphScore)
		article.FinalScore = roundTo4(finalScore)
		article.Reason = reason
		article.Relations = relations
		article.ScoreDetails = types.ScoreDetails{
			EsScore:       roundTo4(normalizedEsScore),
			GraphScore:    roundTo4(graphScore),
			BusinessScore: 0,
			RecencyScore:  0,
		}
	}

	// 按 finalScore 降序排序
	sort.Slice(articles, func(i, j int) bool {
		return articles[i].FinalScore > articles[j].FinalScore
	})

	return articles
}

func roundTo4(v float64) float64 {
	return float64(int(v*10000)) / 10000
}
