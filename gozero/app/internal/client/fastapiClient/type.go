package fastapiClient

// GraphEnhanceRequest 图谱增强请求
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

// GraphRelation 图谱关系
type GraphRelation struct {
	Type   string  `json:"type"`
	Name   string  `json:"name"`
	Score  float64 `json:"score"`
	Reason string  `json:"reason"`
}

// GraphEnhanceItem 图谱增强条目
type GraphEnhanceItem struct {
	ArticleID    int64           `json:"articleId"`
	GraphScore   float64         `json:"graphScore"`
	Reason       string          `json:"reason"`
	Relations    []GraphRelation `json:"relations"`
	MatchedTags  []string        `json:"matchedTags"`
	MatchedPaths []string        `json:"matchedPaths"`
}

// GraphEnhanceResponse 图谱增强响应
type GraphEnhanceResponse struct {
	Items []GraphEnhanceItem `json:"items"`
}

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

// VectorMatchedChunk 向量匹配的文本块
type VectorMatchedChunk struct {
	ArticleID  int64   `json:"articleId"`
	Title      string  `json:"title"`
	ChunkIndex int     `json:"chunkIndex"`
	Score      float64 `json:"score"`
	Content    string  `json:"content"`
}

// VectorEnhanceItem 向量增强条目
type VectorEnhanceItem struct {
	ArticleID     int64                `json:"articleId"`
	VectorScore   float64              `json:"vectorScore"`
	Reason        string               `json:"reason"`
	MatchedChunks []VectorMatchedChunk `json:"matchedChunks"`
}

// VectorEnhanceResponse 向量增强响应
type VectorEnhanceResponse struct {
	Items []VectorEnhanceItem `json:"items"`
}
