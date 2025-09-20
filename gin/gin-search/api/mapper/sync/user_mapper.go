package sync

import (
	"encoding/json"
	"fmt"
	"net/http"
	"search/common/client"
	"search/config"
	"search/entity/po"
	"strings"

	"github.com/gin-gonic/gin"
)

type UserMapper struct{}

func (m *UserMapper) SearchUserByIds(c *gin.Context, userIDs []int) []po.User {
	// 将[]int转换为逗号分隔的字符串
	idStrings := make([]string, len(userIDs))
	for i, id := range userIDs {
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
	result, err := sd.CallService(c, "spring", "/users/batch/:ids", opts)
	if err != nil {
		panic(err.Error())
	}

	// 解析result.Data中的用户列表
	var users []po.User
	var data struct {
		Total int       `json:"total"`
		List  []po.User `json:"list"`
	}
	dataBytes, _ := json.Marshal(result.Data)
	if err := json.Unmarshal(dataBytes, &data); err != nil {
		// 如果直接解析失败，尝试解析为数组
		if err := json.Unmarshal(dataBytes, &users); err != nil {
			panic(fmt.Sprintf("用户数据解析失败: %v, 数据: %s", err, string(dataBytes)))
		}
	} else {
		users = data.List
	}

	return users
}
