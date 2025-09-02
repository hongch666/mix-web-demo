package utils

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// RespondSuccess 返回成功响应
func RespondSuccess(c *gin.Context, data interface{}) {
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
