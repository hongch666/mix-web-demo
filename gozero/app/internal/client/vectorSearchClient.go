package client

import (
	"context"
	"fmt"

	"app/common/client"
	"app/common/utils"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
)

// VectorEnhanceRequest 向量增强请求
type VectorEnhanceRequest struct {
	UserID          int64    `json:"userId"`
	Keyword         string   `json:"keyword"`
	ArticleIDs      []int64  `json:"articleIds"`
	CategoryName    string   `json:"categoryName"`
	SubCategoryName string   `json:"subCategoryName"`
	Tags            []string `json:"tags"`
	Limit           int      `json:"limit"`
	TopK            int      `json:"topK"`
	Mode            string   `json:"mode"`
}

type VectorMatchedChunk struct {
	ArticleID  int64   `json:"articleId"`
	Title      string  `json:"title"`
	ChunkIndex int     `json:"chunkIndex"`
	Score      float64 `json:"score"`
	Content    string  `json:"content"`
}

type VectorEnhanceItem struct {
	ArticleID     int64                `json:"articleId"`
	VectorScore   float64              `json:"vectorScore"`
	Reason        string               `json:"reason"`
	MatchedChunks []VectorMatchedChunk `json:"matchedChunks"`
}

type VectorEnhanceResponse struct {
	Items []VectorEnhanceItem `json:"items"`
}

type VectorSearchClient struct {
	serviceName  string
	namingClient naming_client.INamingClient
}

// NewVectorSearchClient 创建向量搜索客户端
func NewVectorSearchClient(nc naming_client.INamingClient) *VectorSearchClient {
	return &VectorSearchClient{
		serviceName:  "fastapi",
		namingClient: nc,
	}
}

// Enhance 调用 FastAPI 向量增强接口
func (c *VectorSearchClient) Enhance(ctx context.Context, req *VectorEnhanceRequest) (*VectorEnhanceResponse, error) {
	if len(req.ArticleIDs) == 0 || req.Keyword == "" {
		return &VectorEnhanceResponse{Items: []VectorEnhanceItem{}}, nil
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
		"topK":            req.TopK,
		"mode":            req.Mode,
	}

	result, err := sd.CallService(ctx, c.serviceName, "/vector-search/enhance", client.RequestOptions{
		Method:   "POST",
		BodyData: bodyData,
	})
	if err != nil {
		return nil, fmt.Errorf(utils.VECTOR_ENHANCE_CALL_FAILED, err)
	}

	data, ok := result.Data.(map[string]any)
	if !ok {
		return nil, fmt.Errorf(utils.PARSE_ERR + ": " + utils.VECTOR_ENHANCE_RESPONSE_FORMAT_ERROR)
	}

	itemsRaw, ok := data["items"].([]any)
	if !ok {
		return &VectorEnhanceResponse{Items: []VectorEnhanceItem{}}, nil
	}

	items := make([]VectorEnhanceItem, 0, len(itemsRaw))
	for _, itemRaw := range itemsRaw {
		itemMap, ok := itemRaw.(map[string]any)
		if !ok {
			continue
		}

		articleID, _ := toInt64(itemMap["articleId"])
		vectorScore, _ := toFloat64(itemMap["vectorScore"])
		reason, _ := toString(itemMap["reason"])

		items = append(items, VectorEnhanceItem{
			ArticleID:     articleID,
			VectorScore:   vectorScore,
			Reason:        reason,
			MatchedChunks: parseVectorMatchedChunks(itemMap["matchedChunks"]),
		})
	}

	return &VectorEnhanceResponse{Items: items}, nil
}

func parseVectorMatchedChunks(v any) []VectorMatchedChunk {
	rawList, ok := v.([]any)
	if !ok {
		return []VectorMatchedChunk{}
	}

	chunks := make([]VectorMatchedChunk, 0, len(rawList))
	for _, raw := range rawList {
		m, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		articleID, _ := toInt64(m["articleId"])
		title, _ := toString(m["title"])
		chunkIndex64, _ := toInt64(m["chunkIndex"])
		score, _ := toFloat64(m["score"])
		content, _ := toString(m["content"])
		chunks = append(chunks, VectorMatchedChunk{
			ArticleID:  articleID,
			Title:      title,
			ChunkIndex: int(chunkIndex64),
			Score:      score,
			Content:    content,
		})
	}
	return chunks
}
