package client

import (
	"context"
	"fmt"

	"app/common/client"
	"app/common/utils"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
)

// 内部类型定义（不与 types 包耦合，避免循环依赖）
type GraphEnhanceRequest struct {
	UserID          int64    `json:"userId"`
	Keyword         string   `json:"keyword"`
	ArticleIDs      []int64  `json:"articleIds"`
	CategoryName    string   `json:"categoryName"`
	SubCategoryName string   `json:"subCategoryName"`
	Tags            []string `json:"tags"`
	Limit           int      `json:"limit"`
	Mode            string   `json:"mode"`
}

type GraphRelation struct {
	Type   string  `json:"type"`
	Name   string  `json:"name"`
	Score  float64 `json:"score"`
	Reason string  `json:"reason"`
}

type GraphEnhanceItem struct {
	ArticleID    int64           `json:"articleId"`
	GraphScore   float64         `json:"graphScore"`
	Reason       string          `json:"reason"`
	Relations    []GraphRelation `json:"relations"`
	MatchedTags  []string        `json:"matchedTags"`
	MatchedPaths []string        `json:"matchedPaths"`
}

type GraphEnhanceResponse struct {
	Items []GraphEnhanceItem `json:"items"`
}

type GraphSearchClient struct {
	serviceName  string
	namingClient naming_client.INamingClient
}

// NewGraphSearchClient 创建图谱搜索客户端
func NewGraphSearchClient(nc naming_client.INamingClient) *GraphSearchClient {
	return &GraphSearchClient{
		serviceName:  "fastapi",
		namingClient: nc,
	}
}

// Enhance 调用 FastAPI 图谱增强接口
func (c *GraphSearchClient) Enhance(ctx context.Context, req *GraphEnhanceRequest) (*GraphEnhanceResponse, error) {
	if len(req.ArticleIDs) == 0 {
		return &GraphEnhanceResponse{Items: []GraphEnhanceItem{}}, nil
	}

	sd := client.NewServiceDiscovery(c.namingClient)
	bodyData := map[string]any{
		"userId":          req.UserID,
		"keyword":         req.Keyword,
		"articleIds":      req.ArticleIDs,
		"categoryName":    req.CategoryName,
		"subCategoryName": req.SubCategoryName,
		"tags":            req.Tags,
		"limit":           req.Limit,
		"mode":            req.Mode,
	}

	result, err := sd.CallService(ctx, c.serviceName, "/graph-search/enhance", client.RequestOptions{
		Method:   "POST",
		BodyData: bodyData,
	})
	if err != nil {
		return nil, fmt.Errorf(utils.GRAPH_ENHANCE_CALL_FAILED, err)
	}

	// 解析返回数据
	data, ok := result.Data.(map[string]any)
	if !ok {
		return nil, fmt.Errorf(utils.PARSE_ERR + ": " + utils.GRAPH_ENHANCE_RESPONSE_FORMAT_ERROR)
	}

	itemsRaw, ok := data["items"].([]any)
	if !ok {
		return &GraphEnhanceResponse{Items: []GraphEnhanceItem{}}, nil
	}

	items := make([]GraphEnhanceItem, 0, len(itemsRaw))
	for _, itemRaw := range itemsRaw {
		itemMap, ok := itemRaw.(map[string]any)
		if !ok {
			continue
		}

		articleID, _ := toInt64(itemMap["articleId"])
		graphScore, _ := toFloat64(itemMap["graphScore"])
		reason, _ := toString(itemMap["reason"])

		relations := parseRelations(itemMap["relations"])
		matchedTags := parseStringSlice(itemMap["matchedTags"])
		matchedPaths := parseStringSlice(itemMap["matchedPaths"])

		items = append(items, GraphEnhanceItem{
			ArticleID:    articleID,
			GraphScore:   graphScore,
			Reason:       reason,
			Relations:    relations,
			MatchedTags:  matchedTags,
			MatchedPaths: matchedPaths,
		})
	}

	return &GraphEnhanceResponse{Items: items}, nil
}

func toInt64(v any) (int64, bool) {
	switch val := v.(type) {
	case float64:
		return int64(val), true
	case int64:
		return val, true
	case int:
		return int64(val), true
	default:
		return 0, false
	}
}

func toFloat64(v any) (float64, bool) {
	switch val := v.(type) {
	case float64:
		return val, true
	case int:
		return float64(val), true
	case int64:
		return float64(val), true
	default:
		return 0, false
	}
}

func toString(v any) (string, bool) {
	s, ok := v.(string)
	return s, ok
}

func parseRelations(v any) []GraphRelation {
	rawList, ok := v.([]any)
	if !ok {
		return []GraphRelation{}
	}

	relations := make([]GraphRelation, 0, len(rawList))
	for _, raw := range rawList {
		m, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		relType, _ := toString(m["type"])
		name, _ := toString(m["name"])
		score, _ := toFloat64(m["score"])
		reason, _ := toString(m["reason"])
		relations = append(relations, GraphRelation{
			Type:   relType,
			Name:   name,
			Score:  score,
			Reason: reason,
		})
	}
	return relations
}

func parseStringSlice(v any) []string {
	rawList, ok := v.([]any)
	if !ok {
		return nil
	}
	result := make([]string, 0, len(rawList))
	for _, item := range rawList {
		if s, ok := item.(string); ok {
			result = append(result, s)
		}
	}
	return result
}
