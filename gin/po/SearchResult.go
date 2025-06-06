package po

type SearchResult struct {
	Total int         `json:"total"`
	List  []ArticleES `json:"list"`
}
