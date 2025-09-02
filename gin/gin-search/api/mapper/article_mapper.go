package mapper

import (
	"encoding/json"
	"gin_proj/common/client"
	"gin_proj/config"
	"gin_proj/entity/po"
	"net/http"

	"github.com/gin-gonic/gin"
)

func SearchArticles(c *gin.Context) []po.Article {
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
