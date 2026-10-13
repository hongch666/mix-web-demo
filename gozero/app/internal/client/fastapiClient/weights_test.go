package fastapiClient

import (
	"testing"

	"app/model/search"
)

// 全部已知权重键都要落到对应字段，避免某个键被漏掉后长期取默认值
func TestParseWeightsMapsEveryKnownKey(t *testing.T) {
	items := []ScoreWeightItem{
		{Key: "es_score_weight", Value: 1},
		{Key: "ai_rating_weight", Value: 2},
		{Key: "user_rating_weight", Value: 3},
		{Key: "views_weight", Value: 4},
		{Key: "likes_weight", Value: 5},
		{Key: "collects_weight", Value: 6},
		{Key: "author_follow_weight", Value: 7},
		{Key: "recency_weight", Value: 8},
		{Key: "max_views_normalized", Value: 9},
		{Key: "max_likes_normalized", Value: 10},
		{Key: "max_collects_normalized", Value: 11},
		{Key: "max_follows_normalized", Value: 12},
		{Key: "recency_decay_days", Value: 13},
		{Key: "vector_score_weight", Value: 14},
		{Key: "graph_score_weight", Value: 15},
		{Key: "hybrid_min_es_weight", Value: 16},
	}

	got, err := parseWeights(items)
	if err != nil {
		t.Fatalf("解析权重失败: %v", err)
	}

	want := search.SearchWeights{
		ESScoreWeight:         1,
		AIRatingWeight:        2,
		UserRatingWeight:      3,
		ViewsWeight:           4,
		LikesWeight:           5,
		CollectsWeight:        6,
		AuthorFollowWeight:    7,
		RecencyWeight:         8,
		MaxViewsNormalized:    9,
		MaxLikesNormalized:    10,
		MaxCollectsNormalized: 11,
		MaxFollowsNormalized:  12,
		RecencyDecayDays:      13,
		VectorScoreWeight:     14,
		GraphScoreWeight:      15,
		HybridMinESWeight:     16,
	}
	if got != want {
		t.Fatalf("权重解析结果 = %+v，期望 %+v", got, want)
	}
}

// 未知权重键必须报错：FastAPI 改了键名时不能静默把该权重当成 0
func TestParseWeightsRejectsUnknownKey(t *testing.T) {
	if _, err := parseWeights([]ScoreWeightItem{{Key: "unknown_weight", Value: 1}}); err == nil {
		t.Fatal("未知权重键应返回解析错误")
	}
}

// 权重接口正常响应
func TestParseSearchWeightsReadsWeightsField(t *testing.T) {
	got, err := parseSearchWeights(map[string]any{
		"weights": []any{
			map[string]any{"key": "es_score_weight", "value": 0.4, "description": "ES 基础分权重"},
			map[string]any{"key": "recency_decay_days", "value": 30, "description": "时间衰减天数"},
		},
	})
	if err != nil {
		t.Fatalf("解析权重响应失败: %v", err)
	}
	if got.ESScoreWeight != 0.4 || got.RecencyDecayDays != 30 {
		t.Fatalf("权重解析结果 = %+v", got)
	}
}

// weights 字段缺失必须报错，否则会得到 16 个全零权重且没有任何日志
func TestParseSearchWeightsRejectsMissingField(t *testing.T) {
	cases := []struct {
		name string
		data any
	}{
		{name: "顶层不是对象", data: []any{}},
		{name: "weights 字段缺失", data: map[string]any{"other": 1}},
		{name: "weights 不是数组", data: map[string]any{"weights": map[string]any{}}},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if _, err := parseSearchWeights(c.data); err == nil {
				t.Fatalf("应返回解析错误: %#v", c.data)
			}
		})
	}
}

// 脚本接口正常响应
func TestParseSearchScriptReadsEsScript(t *testing.T) {
	got, err := parseSearchScript(map[string]any{"es_script": "return params.esWeight"})
	if err != nil {
		t.Fatalf("解析脚本响应失败: %v", err)
	}
	if got.EsScript != "return params.esWeight" {
		t.Fatalf("脚本内容 = %q", got.EsScript)
	}
}

// es_script 缺失、为空或类型不符都必须报错，不能把空脚本交给 ES
func TestParseSearchScriptRejectsInvalidScript(t *testing.T) {
	cases := []struct {
		name string
		data any
	}{
		{name: "顶层不是对象", data: "invalid"},
		{name: "es_script 字段缺失", data: map[string]any{"other": "x"}},
		{name: "es_script 为空字符串", data: map[string]any{"es_script": ""}},
		{name: "es_script 类型不符", data: map[string]any{"es_script": 1}},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if _, err := parseSearchScript(c.data); err == nil {
				t.Fatalf("应返回解析错误: %#v", c.data)
			}
		})
	}
}

// 脚本参数名映射正常响应
func TestParseSearchScriptParamsReadsMapping(t *testing.T) {
	got, err := parseSearchScriptParams(map[string]any{
		"script_params": []any{
			map[string]any{"weight_key": "es_score_weight", "param_name": "esWeight"},
			map[string]any{"weight_key": "views_weight", "param_name": "viewsWeight"},
		},
	})
	if err != nil {
		t.Fatalf("解析脚本参数映射失败: %v", err)
	}
	if got["es_score_weight"] != "esWeight" || got["views_weight"] != "viewsWeight" {
		t.Fatalf("脚本参数映射 = %+v", got)
	}
}

// script_params 字段缺失必须报错，否则权重无法绑定到脚本参数
func TestParseSearchScriptParamsRejectsMissingField(t *testing.T) {
	cases := []struct {
		name string
		data any
	}{
		{name: "顶层不是对象", data: []any{}},
		{name: "script_params 字段缺失", data: map[string]any{"other": 1}},
		{name: "script_params 不是数组", data: map[string]any{"script_params": "invalid"}},
	}

	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if _, err := parseSearchScriptParams(c.data); err == nil {
				t.Fatalf("应返回解析错误: %#v", c.data)
			}
		})
	}
}
