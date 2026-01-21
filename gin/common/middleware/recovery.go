package middleware

import (
	"fmt"
	"runtime/debug"

	"gin_proj/common/exceptions"
	"gin_proj/common/utils"

	"github.com/gin-gonic/gin"
)

func RecoveryMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		defer func() {
			if err := recover(); err != nil {
				stack := string(debug.Stack())

				// 判断是否是业务异常（可向客户端显示）
				if businessErr, ok := err.(*exceptions.BusinessError); ok {
					// 业务异常：返回对应的错误信息，记录详细堆栈
					utils.FileLogger.Error(fmt.Sprintf("business error: %s\nerror detail: %s\n%s", businessErr.Message, businessErr.Err, stack))
					utils.RespondError(c, 200, businessErr.Message)
				} else {
					// 其他异常：返回固定的错误信息，记录详细堆栈
					utils.FileLogger.Error(fmt.Sprintf("堆栈错误信息: %v\n%s", err, stack))
					utils.RespondError(c, 200, "Gin服务器错误")
				}
				c.Abort()
			}
		}()
		c.Next()
	}
}
