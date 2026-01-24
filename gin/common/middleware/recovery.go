package middleware

import (
	"fmt"
	"net/http"
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
					utils.FileLogger.Error(fmt.Sprintf(utils.BUSINESS_ERROR_MESSAGE, businessErr.Message, businessErr.Err, stack))
					utils.RespondError(c, http.StatusOK, businessErr.Message)
				} else {
					// 其他异常：返回固定的错误信息，记录详细堆栈
					utils.FileLogger.Error(fmt.Sprintf(utils.STACK_ERROR_MESSAGE, err, stack))
					utils.RespondError(c, http.StatusOK, utils.UNIFIED_ERROR_RESPONSE_MESSAGE)
				}
				c.Abort()
			}
		}()
		c.Next()
	}
}
