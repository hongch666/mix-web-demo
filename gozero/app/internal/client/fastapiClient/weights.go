package fastapiClient

import (
	"context"
	"encoding/json"
	"fmt"

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

// GetSearchWeights 从 FastAPI 获取搜索权重，走本地加 Redis 两级缓存，回源失败时降级返回本地旧值
func (c *FastapiClient) GetSearchWeights(ctx context.Context) (search.SearchWeights, error) {
	return c.searchWeightsCache.Get(ctx, constants.SEARCH_CONFIG_WEIGHTS_CACHE_KEY, func(loadCtx context.Context) (search.SearchWeights, error) {
		result, err := c.serviceDisc.CallService(loadCtx, c.serviceName, "/algorithm/search/weights", client.RequestOptions{
			Method: "GET",
		})
		if err != nil {
			return search.SearchWeights{}, err
		}
		return parseSearchWeights(result.Data)
	})
}

// GetSearchScript 从 FastAPI 获取 ES 搜索脚本模板，走本地加 Redis 两级缓存
// 返回使用 params.xxx 占位符的 Painless 脚本，由调用方通过 elastic.NewScript(script).Param(...) 传入权重后使用
func (c *FastapiClient) GetSearchScript(ctx context.Context) (search.SearchScript, error) {
	return c.searchScriptCache.Get(ctx, constants.SEARCH_CONFIG_SCRIPT_CACHE_KEY, func(loadCtx context.Context) (search.SearchScript, error) {
		result, err := c.serviceDisc.CallService(loadCtx, c.serviceName, "/algorithm/search/script", client.RequestOptions{
			Method: "GET",
		})
		if err != nil {
			return search.SearchScript{}, err
		}
		return parseSearchScript(result.Data)
	})
}

// GetSearchScriptParams 从 FastAPI 获取脚本参数名映射，走本地加 Redis 两级缓存
// 返回 weight_key → script_param_name 的映射关系，告诉 GoZero 每个权重值在 Painless 脚本中对应的 params.xxx 参数名
func (c *FastapiClient) GetSearchScriptParams(ctx context.Context) (search.ScriptParamMapping, error) {
	return c.searchScriptParamsCache.Get(ctx, constants.SEARCH_CONFIG_SCRIPT_PARAMS_CACHE_KEY, func(loadCtx context.Context) (search.ScriptParamMapping, error) {
		result, err := c.serviceDisc.CallService(loadCtx, c.serviceName, "/algorithm/search/script-params", client.RequestOptions{
			Method: "GET",
		})
		if err != nil {
			return nil, err
		}
		return parseSearchScriptParams(result.Data)
	})
}
