package fastapiClient

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"app/common/client"
	"app/common/constants"
	"app/model/search"
)

// ScoreWeightItem FastAPI 返回的单个权重项
type ScoreWeightItem struct {
	Key         string  `json:"key"`
	Value       float64 `json:"value"`
	Description string  `json:"description"`
}

// parseWeights 从 key-value 列表解析为结构化权重
func parseWeights(items []ScoreWeightItem) search.SearchWeights {
	w := search.SearchWeights{}
	for _, item := range items {
		switch item.Key {
		case "es_score_weight":
			w.ESScoreWeight = item.Value
		case "ai_rating_weight":
			w.AIRatingWeight = item.Value
		case "user_rating_weight":
			w.UserRatingWeight = item.Value
		case "views_weight":
			w.ViewsWeight = item.Value
		case "likes_weight":
			w.LikesWeight = item.Value
		case "collects_weight":
			w.CollectsWeight = item.Value
		case "author_follow_weight":
			w.AuthorFollowWeight = item.Value
		case "recency_weight":
			w.RecencyWeight = item.Value
		case "max_views_normalized":
			w.MaxViewsNormalized = item.Value
		case "max_likes_normalized":
			w.MaxLikesNormalized = item.Value
		case "max_collects_normalized":
			w.MaxCollectsNormalized = item.Value
		case "max_follows_normalized":
			w.MaxFollowsNormalized = item.Value
		case "recency_decay_days":
			w.RecencyDecayDays = int64(item.Value)
		case "vector_score_weight":
			w.VectorScoreWeight = item.Value
		case "graph_score_weight":
			w.GraphScoreWeight = item.Value
		case "hybrid_min_es_weight":
			w.HybridMinESWeight = item.Value
		}
	}
	return w
}

// 全局权重缓存
var (
	cachedWeights     *search.SearchWeights
	weightsCacheMutex sync.RWMutex
	weightsLastFetch  time.Time
	weightCacheTTL    = 60 * time.Second
)

// GetSearchWeights 从 FastAPI 获取搜索权重（缓存 60s）
func (c *FastapiClient) GetSearchWeights(ctx context.Context) (search.SearchWeights, error) {
	// 读缓存
	weightsCacheMutex.RLock()
	if cachedWeights != nil && time.Since(weightsLastFetch) < weightCacheTTL {
		w := *cachedWeights
		weightsCacheMutex.RUnlock()
		return w, nil
	}
	weightsCacheMutex.RUnlock()

	// 调用 FastAPI
	result, err := c.serviceDisc.CallService(ctx, c.serviceName, "/algorithm/search/weights", client.RequestOptions{
		Method: "GET",
	})
	if err != nil {
		// FastAPI 不可用时返回旧缓存（如果存在）
		weightsCacheMutex.RLock()
		if cachedWeights != nil {
			w := *cachedWeights
			weightsCacheMutex.RUnlock()
			return w, nil
		}
		weightsCacheMutex.RUnlock()
		return search.SearchWeights{}, err
	}

	// 解析响应
	dataMap, ok := result.Data.(map[string]any)
	if !ok {
		return search.SearchWeights{}, fmt.Errorf(constants.FASTAPI_WEIGHTS_FORMAT_ERROR)
	}
	weightsRaw, _ := json.Marshal(dataMap["weights"])
	var items []ScoreWeightItem
	if err := json.Unmarshal(weightsRaw, &items); err != nil {
		return search.SearchWeights{}, err
	}

	w := parseWeights(items)

	// 写缓存
	weightsCacheMutex.Lock()
	cachedWeights = &w
	weightsLastFetch = time.Now()
	weightsCacheMutex.Unlock()

	return w, nil
}
