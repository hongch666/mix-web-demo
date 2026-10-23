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

// ScriptParamItem FastAPI 返回的脚本参数名映射项，告知 GoZero 每个权重 key 在 Painless 脚本中对应的 params.xxx 参数名
type ScriptParamItem struct {
	WeightKey   string `json:"weight_key"`
	ParamName   string `json:"param_name"`
	Description string `json:"description"`
}

// parseWeights 从 key-value 列表解析为结构化权重，出现未知权重键时返回错误：静默忽略会让该权重长期为 0，且不会留下任何日志
func parseWeights(items []ScoreWeightItem) (search.SearchWeights, error) {
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
		default:
			return search.SearchWeights{}, fmt.Errorf(constants.FASTAPI_WEIGHTS_UNKNOWN_KEY, item.Key)
		}
	}
	return w, nil
}

// parseSearchWeights 解析权重接口响应，weights 字段缺失或格式不符时返回错误
func parseSearchWeights(data any) (search.SearchWeights, error) {
	dataMap, ok := data.(map[string]any)
	if !ok {
		return search.SearchWeights{}, fmt.Errorf(constants.FASTAPI_RESPONSE_FORMAT_ERROR)
	}

	// weights 字段缺失时 json.Unmarshal 会得到 nil 切片且不报错，一旦放过就是 16 个权重全为 0
	weightsValue, ok := dataMap["weights"]
	if !ok {
		return search.SearchWeights{}, fmt.Errorf(constants.FASTAPI_WEIGHTS_INVALID)
	}

	weightsRaw, err := json.Marshal(weightsValue)
	if err != nil {
		return search.SearchWeights{}, fmt.Errorf(constants.RESPONSE_DATA_SERIALIZE, err)
	}

	var items []ScoreWeightItem
	if err := json.Unmarshal(weightsRaw, &items); err != nil {
		return search.SearchWeights{}, fmt.Errorf(constants.RESPONSE_DATA_DESERIALIZE, err)
	}

	return parseWeights(items)
}

// parseSearchScript 解析搜索脚本接口响应，es_script 缺失、非字符串或为空时返回错误
func parseSearchScript(data any) (search.SearchScript, error) {
	dataMap, ok := data.(map[string]any)
	if !ok {
		return search.SearchScript{}, fmt.Errorf(constants.FASTAPI_RESPONSE_FORMAT_ERROR)
	}

	esScript, ok := dataMap["es_script"].(string)
	if !ok || esScript == "" {
		return search.SearchScript{}, fmt.Errorf(constants.FASTAPI_SCRIPT_INVALID)
	}

	return search.SearchScript{EsScript: esScript}, nil
}

// parseSearchScriptParams 解析脚本参数名映射接口响应，script_params 字段缺失或格式不符时返回错误
func parseSearchScriptParams(data any) (search.ScriptParamMapping, error) {
	dataMap, ok := data.(map[string]any)
	if !ok {
		return nil, fmt.Errorf(constants.FASTAPI_RESPONSE_FORMAT_ERROR)
	}

	paramsValue, ok := dataMap["script_params"]
	if !ok {
		return nil, fmt.Errorf(constants.FASTAPI_SCRIPT_PARAMS_INVALID)
	}

	paramsRaw, err := json.Marshal(paramsValue)
	if err != nil {
		return nil, fmt.Errorf(constants.RESPONSE_DATA_SERIALIZE, err)
	}

	var items []ScriptParamItem
	if err := json.Unmarshal(paramsRaw, &items); err != nil {
		return nil, fmt.Errorf(constants.RESPONSE_DATA_DESERIALIZE, err)
	}

	// 构建 weight_key → param_name 映射
	paramMap := make(search.ScriptParamMapping, len(items))
	for _, item := range items {
		paramMap[item.WeightKey] = item.ParamName
	}

	return paramMap, nil
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

// 全局脚本参数名映射缓存
var (
	cachedScriptParams     *search.ScriptParamMapping
	scriptParamsCacheMutex sync.RWMutex
	scriptParamsLastFetch  time.Time
	scriptParamsCacheTTL   = 60 * time.Second
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

	// 解析响应：结构不符必须报错，静默取零权重会让排序失去依据
	w, err := parseSearchWeights(result.Data)
	if err != nil {
		return search.SearchWeights{}, err
	}

	// 写缓存
	weightsCacheMutex.Lock()
	cachedWeights = &w
	weightsLastFetch = time.Now()
	weightsCacheMutex.Unlock()

	return w, nil
}

// GetSearchScript 从 FastAPI 获取 ES 搜索脚本模板（缓存 60s），返回使用 params.xxx 占位符的 Painless 脚本，由调用方通过 elastic.NewScript(script).Param(...) 传入权重后使用
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

	// 解析响应：脚本缺失或为空时整条增强链路都应显式降级，而不是把空脚本交给 ES
	s, err := parseSearchScript(result.Data)
	if err != nil {
		return search.SearchScript{}, err
	}

	// 写缓存
	scriptCacheMutex.Lock()
	cachedScript = &s
	scriptLastFetch = time.Now()
	scriptCacheMutex.Unlock()

	return s, nil
}

// GetSearchScriptParams 从 FastAPI 获取脚本参数名映射（缓存 60s）
// 返回 weight_key → script_param_name 的映射关系，告诉 GoZero 每个权重值在 Painless 脚本中对应的 params.xxx 参数名
// 当 FastAPI 修改脚本参数名时，GoZero 无需修改代码即可自适应
func (c *FastapiClient) GetSearchScriptParams(ctx context.Context) (search.ScriptParamMapping, error) {
	// 读缓存
	scriptParamsCacheMutex.RLock()
	if cachedScriptParams != nil && time.Since(scriptParamsLastFetch) < scriptParamsCacheTTL {
		pm := *cachedScriptParams
		scriptParamsCacheMutex.RUnlock()
		return pm, nil
	}
	scriptParamsCacheMutex.RUnlock()

	// 调用 FastAPI
	result, err := c.serviceDisc.CallService(ctx, c.serviceName, "/algorithm/search/script-params", client.RequestOptions{
		Method: "GET",
	})
	if err != nil {
		// FastAPI 不可用时返回旧缓存（如果存在）
		scriptParamsCacheMutex.RLock()
		if cachedScriptParams != nil {
			pm := *cachedScriptParams
			scriptParamsCacheMutex.RUnlock()
			return pm, nil
		}
		scriptParamsCacheMutex.RUnlock()
		return nil, err
	}

	// 解析响应：映射缺失时权重无法绑定到脚本参数，必须显式降级
	paramMap, err := parseSearchScriptParams(result.Data)
	if err != nil {
		return nil, err
	}

	// 写缓存
	scriptParamsCacheMutex.Lock()
	cachedScriptParams = &paramMap
	scriptParamsLastFetch = time.Now()
	scriptParamsCacheMutex.Unlock()

	return paramMap, nil
}
