package fastapiClient

import (
	"context"

	"app/common/client"
	"app/model/search"
)

// Client 定义 GoZero 使用的 FastAPI 调用契约，便于业务层隔离远程依赖
type Client interface {
	EnhanceGraph(context.Context, *GraphEnhanceRequest) (client.Result, error)
	EnhanceVector(context.Context, *VectorEnhanceRequest) (client.Result, error)
	GetSearchWeights(context.Context) (search.SearchWeights, error)
	GetSearchScript(context.Context) (search.SearchScript, error)
	GetSearchScriptParams(context.Context) (search.ScriptParamMapping, error)
}

// GraphEnhanceRequest 图谱增强请求
type GraphEnhanceRequest struct {
	UserID          int64    `json:"user_id"`
	Keyword         string   `json:"keyword"`
	ArticleIDs      []int64  `json:"article_ids"`
	CategoryName    string   `json:"category_name"`
	SubCategoryName string   `json:"sub_category_name"`
	Tags            []string `json:"tags"`
	Limit           int      `json:"limit"`
	Mode            string   `json:"mode"`
}

// GraphRelation 图谱关系
type GraphRelation struct {
	Type   string  `json:"type"`
	Name   string  `json:"name"`
	Score  float64 `json:"score"`
	Reason string  `json:"reason"`
}

// GraphEnhanceItem 图谱增强条目
type GraphEnhanceItem struct {
	ArticleID    int64           `json:"article_id"`
	GraphScore   float64         `json:"graph_score"`
	Reason       string          `json:"reason"`
	Relations    []GraphRelation `json:"relations"`
	MatchedTags  []string        `json:"matched_tags"`
	MatchedPaths []string        `json:"matched_paths"`
}

// VectorEnhanceRequest 向量增强请求
type VectorEnhanceRequest struct {
	UserID          int64    `json:"user_id"`
	Keyword         string   `json:"keyword"`
	ArticleIDs      []int64  `json:"article_ids"`
	CategoryName    string   `json:"category_name"`
	SubCategoryName string   `json:"sub_category_name"`
	Tags            []string `json:"tags"`
	Limit           int      `json:"limit"`
	TopK            int      `json:"top_k"`
	Mode            string   `json:"mode"`
}

// VectorMatchedChunk 向量匹配的文本块
type VectorMatchedChunk struct {
	ArticleID  int64   `json:"article_id"`
	Title      string  `json:"title"`
	ChunkIndex int     `json:"chunk_index"`
	Score      float64 `json:"score"`
	Content    string  `json:"content"`
}

// VectorEnhanceItem 向量增强条目
type VectorEnhanceItem struct {
	ArticleID     int64                `json:"article_id"`
	VectorScore   float64              `json:"vector_score"`
	Reason        string               `json:"reason"`
	MatchedChunks []VectorMatchedChunk `json:"matched_chunks"`
}
