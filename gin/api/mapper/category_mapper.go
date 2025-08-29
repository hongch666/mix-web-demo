package mapper

import (
	"encoding/json"
	"fmt"
	"gin_proj/common/client"
	"gin_proj/config"
	"gin_proj/entity/po"
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
)

func SearchSubCategoriesByIds(c *gin.Context, subCategoryIDs []int) []po.SubCategory {
	// 将[]int转换为逗号分隔的字符串
	idStrings := make([]string, len(subCategoryIDs))
	for i, id := range subCategoryIDs {
		idStrings[i] = fmt.Sprintf("%d", id)
	}
	idsParam := strings.Join(idStrings, ",")

	opts := client.RequestOptions{
		Method: http.MethodGet,
		PathParams: map[string]string{
			"ids": idsParam,
		},
	}
	sd := client.NewServiceDiscovery(config.NamingClient)
	result, err := sd.CallService(c, "spring", "/category/sub/batch/:ids", opts)
	if err != nil {
		panic(err.Error())
	}

	// 解析result.Data中的子分类列表
	var subCategories []po.SubCategory
	var data struct {
		Total int              `json:"total"`
		List  []po.SubCategory `json:"list"`
	}
	dataBytes, _ := json.Marshal(result.Data)
	if err := json.Unmarshal(dataBytes, &data); err != nil {
		// 如果解析为包含total和list的结构失败，尝试直接解析为数组
		if err := json.Unmarshal(dataBytes, &subCategories); err != nil {
			panic(err.Error())
		}
	} else {
		subCategories = data.List
	}
	return subCategories
}

func SearchCategoriesByIds(c *gin.Context, categoryIDs []int) []po.Category {
	// 将[]int转换为逗号分隔的字符串
	idStrings := make([]string, len(categoryIDs))
	for i, id := range categoryIDs {
		idStrings[i] = fmt.Sprintf("%d", id)
	}
	idsParam := strings.Join(idStrings, ",")

	opts := client.RequestOptions{
		Method: http.MethodGet,
		PathParams: map[string]string{
			"ids": idsParam,
		},
	}
	sd := client.NewServiceDiscovery(config.NamingClient)
	result, err := sd.CallService(c, "spring", "/category/batch/:ids", opts)
	if err != nil {
		panic(err.Error())
	}

	// 解析result.Data中的分类列表
	var categories []po.Category
	var data struct {
		Total int           `json:"total"`
		List  []po.Category `json:"list"`
	}
	dataBytes, _ := json.Marshal(result.Data)
	if err := json.Unmarshal(dataBytes, &data); err != nil {
		// 如果解析为包含total和list的结构失败，尝试直接解析为数组
		if err := json.Unmarshal(dataBytes, &categories); err != nil {
			panic(err.Error())
		}
	} else {
		categories = data.List
	}
	return categories
}
