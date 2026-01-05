package utils

import (
	"encoding/json"
	"net/http"

	"github.com/gin-gonic/gin"
)

// RespondSuccess 返回成功响应
func RespondSuccess(c *gin.Context, data any) {
	c.JSON(http.StatusOK, gin.H{
		"code": 1,
		"msg":  "success",
		"data": data,
	})
	c.Abort()
}

// RespondError 返回错误响应
func RespondError(c *gin.Context, code int, message string) {
	c.JSON(code, gin.H{
		"code": 0,
		"msg":  message,
		"data": nil,
	})
	c.Abort()
}

// ToJSON 将对象转换为JSON字符串
func ToJSON(data any) string {
	jsonBytes, err := json.Marshal(data)
	if err != nil {
		return ""
	}
	return string(jsonBytes)
}
