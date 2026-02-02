package vo

import "github.com/hongch666/mix-web-demo/gin/entity/po"

type SearchVO struct {
	Total int            `json:"total"`
	List  []po.ArticleES `json:"list"`
}
