package search

import (
	"sort"

	"app/internal/client/fastapiClient"
	"app/internal/types"
)

// 融合重排后的文章项
type fusionItem struct {
	esScore        float64
	vectorScore    float64
	graphScore     float64
	finalScore     float64
	reason         string
	semanticReason string
	relations      []fastapiClient.GraphRelation
	matchedChunks  []fastapiClient.VectorMatchedChunk
}

type FusionConfig struct {
	VectorScoreWeight float64
	GraphScoreWeight  float64
	HybridMinESWeight float64
	IsLoggedIn        bool
	HasKeyword        bool
	VectorEnabled     bool
	GraphEnabled      bool
}

// FusionEngine 融合打分配置
type FusionEngine struct {
	esWeight     float64
	vectorWeight float64
	graphWeight  float64
}

// NewFusionEngine 创建融合引擎
func NewFusionEngine(cfg FusionConfig) *FusionEngine {
	vectorWeight := 0.0
	if cfg.VectorEnabled && cfg.HasKeyword && cfg.VectorScoreWeight > 0 {
		vectorWeight = cfg.VectorScoreWeight
	}

	graphWeight := 0.0
	if cfg.GraphEnabled && cfg.GraphScoreWeight > 0 {
		graphWeight = cfg.GraphScoreWeight
	}

	// 根据用户状态调整权重
	if !cfg.IsLoggedIn {
		graphWeight = 0
		if cfg.HasKeyword && cfg.VectorEnabled {
			vectorWeight = max(vectorWeight, 0.30)
		}
	} else if !cfg.HasKeyword {
		vectorWeight = 0
		if cfg.GraphEnabled {
			graphWeight = max(graphWeight, 0.65)
		}
	}

	esWeight := 1.0 - vectorWeight - graphWeight
	if esWeight < cfg.HybridMinESWeight {
		overflow := cfg.HybridMinESWeight - esWeight
		totalEnhancedWeight := vectorWeight + graphWeight
		if totalEnhancedWeight > 0 {
			vectorWeight -= overflow * (vectorWeight / totalEnhancedWeight)
			graphWeight -= overflow * (graphWeight / totalEnhancedWeight)
			if vectorWeight < 0 {
				vectorWeight = 0
			}
			if graphWeight < 0 {
				graphWeight = 0
			}
		}
		esWeight = cfg.HybridMinESWeight
	}

	total := esWeight + vectorWeight + graphWeight
	if total > 0 {
		esWeight /= total
		vectorWeight /= total
		graphWeight /= total
	}

	return &FusionEngine{
		esWeight:     esWeight,
		vectorWeight: vectorWeight,
		graphWeight:  graphWeight,
	}
}

// meanOfVectorItems 计算向量增强结果的均值
// 该均值用于填充未被向量召回的候选，避免把「未匹配」当成零分
func meanOfVectorItems(items []fastapiClient.VectorEnhanceItem) float64 {
	if len(items) == 0 {
		return 0
	}

	sum := 0.0
	for i := range items {
		sum += clamp01(items[i].VectorScore)
	}
	return sum / float64(len(items))
}

// meanOfGraphItems 计算图谱增强结果的均值
// 该均值用于填充未被图谱召回的候选，避免把「无关系」当成零分
func meanOfGraphItems(items []fastapiClient.GraphEnhanceItem) float64 {
	if len(items) == 0 {
		return 0
	}

	sum := 0.0
	for i := range items {
		sum += clamp01(items[i].GraphScore)
	}
	return sum / float64(len(items))
}

// MergeAndRerank 融合 ES、向量和图谱结果并重排
// 入参为整个召回候选集，重排结果由调用方按分页窗口切出目标页，total 始终由 ES 决定
// 归一化分母取候选集内最大 ES 分，故同一召回档位内各页的 FinalScore 可比较
// 未被向量或图谱召回的候选用候选集均值填充，使全部候选处于同一评分量纲
func MergeAndRerank(
	articles []types.ArticleEsItem,
	vectorItems []fastapiClient.VectorEnhanceItem,
	graphItems []fastapiClient.GraphEnhanceItem,
	cfg FusionConfig,
) []types.ArticleEsItem {
	if len(vectorItems) == 0 && len(graphItems) == 0 {
		FillDefaultScores(articles)
		return articles
	}

	vectorMap := make(map[int64]*fastapiClient.VectorEnhanceItem, len(vectorItems))
	for i := range vectorItems {
		item := &vectorItems[i]
		vectorMap[item.ArticleID] = item
	}

	// 构建 articleId -> graphItem 的映射
	graphMap := make(map[int64]*fastapiClient.GraphEnhanceItem, len(graphItems))
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

	// 未被向量或图谱召回的候选用候选集均值填充，避免信号缺失被当成零分而系统性压低排序
	vectorMean := meanOfVectorItems(vectorItems)
	graphMean := meanOfGraphItems(graphItems)

	// 为每篇文章计算最终分
	for i := range articles {
		article := &articles[i]
		normalizedEsScore := 0.0
		if maxEsScore > 0 {
			normalizedEsScore = article.EsScore / maxEsScore
		}

		vectorScore := vectorMean
		semanticReason := ""
		matchedChunks := make([]types.VectorMatchedChunk, 0)
		if vItem, ok := vectorMap[article.Id]; ok {
			vectorScore = clamp01(vItem.VectorScore)
			semanticReason = vItem.Reason
			for _, chunk := range vItem.MatchedChunks {
				matchedChunks = append(matchedChunks, types.VectorMatchedChunk{
					ArticleId:  chunk.ArticleID,
					Title:      chunk.Title,
					ChunkIndex: chunk.ChunkIndex,
					Score:      roundTo4(chunk.Score),
					Content:    chunk.Content,
				})
			}
		}

		graphScore := graphMean
		reason := ""
		relations := make([]types.GraphRelation, 0)
		if gItem, ok := graphMap[article.Id]; ok {
			graphScore = clamp01(gItem.GraphScore)
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

		finalScore := normalizedEsScore*engine.esWeight +
			vectorScore*engine.vectorWeight +
			graphScore*engine.graphWeight

		article.EsScore = roundTo4(normalizedEsScore)
		article.VectorScore = roundTo4(vectorScore)
		article.GraphScore = roundTo4(graphScore)
		article.FinalScore = roundTo4(finalScore)
		article.Reason = reason
		article.SemanticReason = semanticReason
		article.Relations = relations
		article.MatchedChunks = matchedChunks
		article.ScoreDetails = types.ScoreDetails{
			EsScore:       roundTo4(normalizedEsScore),
			VectorScore:   roundTo4(vectorScore),
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

// FillDefaultScores 未启用增强时保留 ES 原排序，同时填充分数字段便于前端统一展示
// 归一化分母同样取候选集内最大 ES 分，与 MergeAndRerank 保持一致
func FillDefaultScores(articles []types.ArticleEsItem) {
	maxEsScore := 0.0
	for _, article := range articles {
		if article.EsScore > maxEsScore {
			maxEsScore = article.EsScore
		}
	}

	for i := range articles {
		normalizedEsScore := 0.0
		if maxEsScore > 0 {
			normalizedEsScore = articles[i].EsScore / maxEsScore
		}
		articles[i].EsScore = roundTo4(normalizedEsScore)
		if articles[i].FinalScore == 0 {
			articles[i].FinalScore = roundTo4(normalizedEsScore)
		}
		if articles[i].Relations == nil {
			articles[i].Relations = make([]types.GraphRelation, 0)
		}
		if articles[i].MatchedChunks == nil {
			articles[i].MatchedChunks = make([]types.VectorMatchedChunk, 0)
		}
		articles[i].ScoreDetails = types.ScoreDetails{
			EsScore:       roundTo4(normalizedEsScore),
			VectorScore:   roundTo4(articles[i].VectorScore),
			GraphScore:    roundTo4(articles[i].GraphScore),
			BusinessScore: 0,
			RecencyScore:  0,
		}
	}
}

func clamp01(v float64) float64 {
	if v < 0 {
		return 0
	}
	if v > 1 {
		return 1
	}
	return v
}

func roundTo4(v float64) float64 {
	return float64(int(v*10000)) / 10000
}
