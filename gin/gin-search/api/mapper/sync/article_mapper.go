package sync

import (
	"encoding/json"
	"net/http"
	"search/common/client"
	"search/config"
	"search/entity/po"

	"github.com/gin-gonic/gin"
)

type ArticleMapper struct{}

func (m *ArticleMapper) SearchArticles(c *gin.Context) []po.Article {
	// 调用Spring部分接口获取文章数据
	opts := client.RequestOptions{
		Method: http.MethodGet,
	}
	sd := client.NewServiceDiscovery(config.NamingClient)
	result, err := sd.CallService(c, "spring", "/articles/list", opts)
	if err != nil {
		panic(err.Error())
	}

	// 解析result.Data中的文章列表
	var articles []po.Article
	var data struct {
		Total int          `json:"total"`
		List  []po.Article `json:"list"`
	}
	dataBytes, _ := json.Marshal(result.Data)
	if err := json.Unmarshal(dataBytes, &data); err != nil {
		panic(err.Error())
	}
	articles = data.List

	return articles
}
