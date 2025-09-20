package middleware

import (
	"chat/common/utils"

	"github.com/gin-gonic/gin"
)

func RecoveryMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		defer func() {
			if err := recover(); err != nil {
				// 转为字符串方便判断
				var errMsg string
				switch e := err.(type) {
				case string:
					errMsg = e
				case error:
					errMsg = e.Error()
				default:
					errMsg = "未知错误"
				}

				// 根据错误信息返回不同响应
				switch errMsg {
				case "not found":
					utils.RespondError(c, 404, "资源未找到")
				case "unauthorized":
					utils.RespondError(c, 401, "未授权")
				default:
					utils.RespondError(c, 500, "出现错误："+errMsg)
				}
				c.Abort()
			}
		}()
		c.Next()
	}
}
