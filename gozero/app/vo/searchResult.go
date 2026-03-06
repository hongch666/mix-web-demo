package vo

import "app/model/articles"

type SearchVO struct {
	Total int                 `json:"total"`
	List  []articles.Articles `json:"list"`
}
