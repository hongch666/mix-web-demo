package middleware

import (
	"context"
	"gin_proj/common/keys"
	"strconv"

	"github.com/gin-gonic/gin"
)

func InjectUserContext() gin.HandlerFunc {
	return func(c *gin.Context) {
		userIDStr := c.GetHeader("X-User-Id")
		username := c.GetHeader("X-Username")

		var userID int64
		if uid, err := strconv.ParseInt(userIDStr, 10, 64); err == nil {
			userID = uid
		}

		// 写入 context
		ctx := context.WithValue(c.Request.Context(), keys.UserIDKey, userID)
		ctx = context.WithValue(ctx, keys.UsernameKey, username)

		// 替换请求上下文
		c.Request = c.Request.WithContext(ctx)
		c.Next()
	}
}
