package middleware

import (
	"log"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/hongch666/mix-web-demo/gin/common/utils"
)

const (
	InternalTokenHeader = "X-Internal-Token"
	BearerPrefix        = "Bearer "
)

// InternalTokenMiddleware 创建内部服务令牌验证中间件
// serviceName: 期望的调用服务名称，为空则不验证服务名称
func InternalTokenMiddleware(serviceName string) gin.HandlerFunc {
	return func(c *gin.Context) {
		// 从请求头中提取内部令牌
		authHeader := c.GetHeader(InternalTokenHeader)
		if authHeader == "" {
			log.Printf("[内部令牌验证] 缺少 %s 请求头，路径: %s", InternalTokenHeader, c.Request.URL.Path)
			c.JSON(400, gin.H{"error": utils.INTERNAL_TOKEN_MISSING})
			c.Abort()
			return
		}

		// 移除 Bearer 前缀
		tokenString := authHeader
		if strings.HasPrefix(authHeader, BearerPrefix) {
			tokenString = authHeader[len(BearerPrefix):]
		}

		if tokenString == "" {
			log.Printf("[内部令牌验证] 令牌为空，路径: %s", c.Request.URL.Path)
			c.JSON(400, gin.H{"error": utils.INTERNAL_TOKEN_MISSING})
			c.Abort()
			return
		}

		// 验证令牌
		tokenUtil := utils.GetTokenUtil()
		claims, err := tokenUtil.ValidateInternalToken(tokenString)
		if err != nil {
			log.Printf("[内部令牌验证] 令牌验证失败: %v, 路径: %s", err, c.Request.URL.Path)
			c.JSON(401, gin.H{"error": utils.INTERNAL_TOKEN_INVALID})
			c.Abort()
			return
		}

		// 检查令牌是否过期
		if claims.ExpiresAt != nil && claims.ExpiresAt.Before(time.Now()) {
			log.Printf("[内部令牌验证] 令牌已过期，路径: %s", c.Request.URL.Path)
			c.JSON(401, gin.H{"error": utils.INTERNAL_TOKEN_EXPIRED})
			c.Abort()
			return
		}

		// 验证服务名称（如果指定了）
		if serviceName != "" && claims.ServiceName != serviceName {
			log.Printf("[内部令牌验证] 服务名不匹配，期望: %s, 实际: %s, 路径: %s", serviceName, claims.ServiceName, c.Request.URL.Path)
			c.JSON(401, gin.H{"error": utils.SERVICE_NAME_MISMATCH})
			c.Abort()
			return
		}

		log.Printf("[内部令牌验证] 验证成功，用户ID: %d, 服务: %s, 路径: %s", claims.UserID, claims.ServiceName, c.Request.URL.Path)
		// 令牌验证成功，继续处理请求
		c.Next()
	}
}

// RequireInternalToken 返回一个中间件，要求内部令牌（不验证服务名称）
func RequireInternalToken() gin.HandlerFunc {
	return InternalTokenMiddleware("")
}

// RequireInternalTokenFromService 返回一个中间件，要求特定服务的内部令牌
func RequireInternalTokenFromService(serviceName string) gin.HandlerFunc {
	return InternalTokenMiddleware(serviceName)
}
