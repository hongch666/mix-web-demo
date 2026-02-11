package utils

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// Success 返回成功响应
func Success(c *gin.Context, data any) {
	c.JSON(http.StatusOK, gin.H{
		"code": 1,
		"msg":  "success",
		"data": data,
	})
	c.Abort()
}

// Error 返回错误响应
func Error(c *gin.Context, code int, message string) {
	c.JSON(code, gin.H{
		"code": 0,
		"msg":  message,
		"data": nil,
	})
	c.Abort()
}
