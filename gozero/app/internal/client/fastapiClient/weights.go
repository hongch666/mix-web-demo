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

// 全局搜索脚本缓存
var (
	cachedScript     *search.SearchScript
	scriptCacheMutex sync.RWMutex
	scriptLastFetch  time.Time
	scriptCacheTTL   = 60 * time.Second
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

// GetSearchScript 从 FastAPI 获取 ES 搜索脚本模板（缓存 60s）
// 返回使用 params.xxx 占位符的 Painless 脚本，由调用方通过 elastic.NewScript(script).Param(...) 传入权重后使用
func (c *FastapiClient) GetSearchScript(ctx context.Context) (search.SearchScript, error) {
	// 读缓存
	scriptCacheMutex.RLock()
	if cachedScript != nil && time.Since(scriptLastFetch) < scriptCacheTTL {
		s := *cachedScript
		scriptCacheMutex.RUnlock()
		return s, nil
	}
	scriptCacheMutex.RUnlock()

	// 调用 FastAPI 新接口
	result, err := c.serviceDisc.CallService(ctx, c.serviceName, "/algorithm/search/script", client.RequestOptions{
		Method: "GET",
	})
	if err != nil {
		// FastAPI 不可用时返回旧缓存（如果存在）
		scriptCacheMutex.RLock()
		if cachedScript != nil {
			s := *cachedScript
			scriptCacheMutex.RUnlock()
			return s, nil
		}
		scriptCacheMutex.RUnlock()
		return search.SearchScript{}, err
	}

	// 解析响应
	dataMap, ok := result.Data.(map[string]any)
	if !ok {
		return search.SearchScript{}, fmt.Errorf(constants.FASTAPI_WEIGHTS_FORMAT_ERROR)
	}
	esScript, _ := dataMap["es_script"].(string)

	s := search.SearchScript{EsScript: esScript}

	// 写缓存
	scriptCacheMutex.Lock()
	cachedScript = &s
	scriptLastFetch = time.Now()
	scriptCacheMutex.Unlock()

	return s, nil
}
