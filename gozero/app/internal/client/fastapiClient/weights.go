package fastapiClient

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"sync"
	"time"

	"app/common/client"
	"app/common/constants"
)

// ScoreWeight 权重配置项
type ScoreWeight struct {
	Key         string  `json:"key"`
	Value       float64 `json:"value"`
	Description string  `json:"description"`
}

// SearchWeights 搜索权重配置
type SearchWeights struct {
	ESEWeight           float64
	AIRatingWeight      float64
	UserRatingWeight    float64
	ViewsWeight         float64
	LikesWeight         float64
	CollectsWeight      float64
	AuthorFollowWeight  float64
	RecencyWeight       float64
	VectorScoreWeight   float64
	GraphInterestWeight float64
	GraphFollowWeight   float64
	GraphSubcatWeight   float64
	GraphKeywordWeight  float64
	MaxViewsNorm        float64
	MaxLikesNorm        float64
	MaxCollectsNorm     float64
	MaxFollowsNorm      float64
	RecencyDecayDays    float64
}

var (
	cachedWeights     *SearchWeights
	weightsCacheMutex sync.RWMutex
	weightsLastFetch  time.Time
	weightCacheTTL    = 60 * time.Second
)

// GetSearchWeights 获取搜索权重配置（优先缓存，过期时调用 FastAPI 刷新）
func (c *FastapiClient) GetSearchWeights(ctx context.Context) (SearchWeights, error) {
	weightsCacheMutex.RLock()
	if cachedWeights != nil && time.Since(weightsLastFetch) < weightCacheTTL {
		w := *cachedWeights
		weightsCacheMutex.RUnlock()
		return w, nil
	}
	weightsCacheMutex.RUnlock()

	result, err := c.serviceDisc.CallService(ctx, c.serviceName, "/algorithm/search/weights", client.RequestOptions{
		Method: "GET",
	})
	if err != nil {
		weightsCacheMutex.RLock()
		if cachedWeights != nil {
			w := *cachedWeights
			weightsCacheMutex.RUnlock()
			return w, nil
		}
		weightsCacheMutex.RUnlock()
		return SearchWeights{}, err
	}

	dataMap, ok := result.Data.(map[string]interface{})
	if !ok {
		return SearchWeights{}, fmt.Errorf(constants.FASTAPI_WEIGHTS_FORMAT_ERROR)
	}
	weightsRaw, _ := json.Marshal(dataMap["weights"])
	var items []ScoreWeight
	if err := json.Unmarshal(weightsRaw, &items); err != nil {
		return SearchWeights{}, err
	}

	w := parseSearchWeights(items)

	weightsCacheMutex.Lock()
	cachedWeights = &w
	weightsLastFetch = time.Now()
	weightsCacheMutex.Unlock()

	return w, nil
}

// GetQueryEmbedding 获取搜索词的嵌入向量
func (c *FastapiClient) GetQueryEmbedding(ctx context.Context, keyword string) ([]float64, error) {
	result, err := c.serviceDisc.CallService(ctx, c.serviceName,
		"/vector-search/embed?"+url.Values{"keyword": {keyword}}.Encode(),
		client.RequestOptions{Method: "GET"},
	)
	if err != nil {
		return nil, err
	}

	dataMap, ok := result.Data.(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf(constants.FASTAPI_EMBED_FORMAT_ERROR)
	}
	vecRaw, ok := dataMap["query_vector"].([]interface{})
	if !ok {
		return nil, fmt.Errorf(constants.FASTAPI_EMBED_DATA_FORMAT_ERROR)
	}
	vec := make([]float64, len(vecRaw))
	for i, v := range vecRaw {
		if f, ok := v.(float64); ok {
			vec[i] = f
		}
	}
	return vec, nil
}

func parseSearchWeights(items []ScoreWeight) SearchWeights {
	w := SearchWeights{}
	for _, item := range items {
		switch item.Key {
		case "es_score_weight":
			w.ESEWeight = item.Value
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
		case "vector_score_weight":
			w.VectorScoreWeight = item.Value
		case "graph_interest_weight":
			w.GraphInterestWeight = item.Value
		case "graph_follow_weight":
			w.GraphFollowWeight = item.Value
		case "graph_subcat_weight":
			w.GraphSubcatWeight = item.Value
		case "graph_keyword_weight":
			w.GraphKeywordWeight = item.Value
		case "max_views_normalized":
			w.MaxViewsNorm = item.Value
		case "max_likes_normalized":
			w.MaxLikesNorm = item.Value
		case "max_collects_normalized":
			w.MaxCollectsNorm = item.Value
		case "max_follows_normalized":
			w.MaxFollowsNorm = item.Value
		case "recency_decay_days":
			w.RecencyDecayDays = item.Value
		}
	}
	return w
}
