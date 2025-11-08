package vo

import "gin_proj/entity/po"

type SearchVO struct {
	Total int            `json:"total"`
	List  []po.ArticleES `json:"list"`
}
