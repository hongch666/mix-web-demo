package middleware

import (
	"log"
	"net/http"
	"strings"
	"time"

	"app/common/utils"
)

const (
	InternalTokenHeader = "X-Internal-Token"
	BearerPrefix        = "Bearer "
)

type InternalServiceMiddleware struct{}

func NewInternalServiceMiddleware() *InternalServiceMiddleware {
	return &InternalServiceMiddleware{}
}

// Handle 处理内部服务令牌验证
// serviceName 为空表示不验证服务名称
func (m *InternalServiceMiddleware) Handle(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// 从请求头中提取内部令牌
		authHeader := r.Header.Get(InternalTokenHeader)
		if authHeader == "" {
			log.Printf("[内部令牌验证] 缺少 %s 请求头，路径: %s", InternalTokenHeader, r.URL.Path)
			http.Error(w, utils.INTERNAL_TOKEN_MISSING, http.StatusBadRequest)
			return
		}

		// 移除 Bearer 前缀
		tokenString := authHeader
		if strings.HasPrefix(authHeader, BearerPrefix) {
			tokenString = authHeader[len(BearerPrefix):]
		}

		if tokenString == "" {
			log.Printf("[内部令牌验证] 令牌为空，路径: %s", r.URL.Path)
			http.Error(w, utils.INTERNAL_TOKEN_MISSING, http.StatusBadRequest)
			return
		}

		// 验证令牌
		tokenUtil := utils.GetTokenUtil()
		claims, err := tokenUtil.ValidateInternalToken(tokenString)
		if err != nil {
			log.Printf("[内部令牌验证] 令牌验证失败: %v, 路径: %s", err, r.URL.Path)
			http.Error(w, utils.INTERNAL_TOKEN_INVALID, http.StatusUnauthorized)
			return
		}

		// 检查令牌是否过期
		if claims.ExpiresAt != nil && claims.ExpiresAt.Before(time.Now()) {
			log.Printf("[内部令牌验证] 令牌已过期，路径: %s", r.URL.Path)
			http.Error(w, utils.INTERNAL_TOKEN_EXPIRED, http.StatusUnauthorized)
			return
		}

		log.Printf("[内部令牌验证] 验证成功，用户ID: %d, 服务: %s, 路径: %s", claims.UserID, claims.ServiceName, r.URL.Path)
		// 令牌验证成功，继续处理请求
		next(w, r)
	}
}

// NewInternalTokenMiddleware 创建需要验证特定服务的中间件
func NewInternalTokenMiddleware(serviceName string) func(http.HandlerFunc) http.HandlerFunc {
	return func(next http.HandlerFunc) http.HandlerFunc {
		return func(w http.ResponseWriter, r *http.Request) {
			// 从请求头中提取内部令牌
			authHeader := r.Header.Get(InternalTokenHeader)
			if authHeader == "" {
				log.Printf("[内部令牌验证] 缺少 %s 请求头，路径: %s", InternalTokenHeader, r.URL.Path)
				http.Error(w, utils.INTERNAL_TOKEN_MISSING, http.StatusBadRequest)
				return
			}

			// 移除 Bearer 前缀
			tokenString := authHeader
			if strings.HasPrefix(authHeader, BearerPrefix) {
				tokenString = authHeader[len(BearerPrefix):]
			}

			if tokenString == "" {
				log.Printf("[内部令牌验证] 令牌为空，路径: %s", r.URL.Path)
				http.Error(w, utils.INTERNAL_TOKEN_MISSING, http.StatusBadRequest)
				return
			}

			// 验证令牌
			tokenUtil := utils.GetTokenUtil()
			claims, err := tokenUtil.ValidateInternalToken(tokenString)
			if err != nil {
				log.Printf("[内部令牌验证] 令牌验证失败: %v, 路径: %s", err, r.URL.Path)
				http.Error(w, utils.INTERNAL_TOKEN_INVALID, http.StatusUnauthorized)
				return
			}

			// 检查令牌是否过期
			if claims.ExpiresAt != nil && claims.ExpiresAt.Before(time.Now()) {
				log.Printf("[内部令牌验证] 令牌已过期，路径: %s", r.URL.Path)
				http.Error(w, utils.INTERNAL_TOKEN_EXPIRED, http.StatusUnauthorized)
				return
			}

			// 验证服务名称（如果指定了）
			if serviceName != "" && claims.ServiceName != serviceName {
				log.Printf("[内部令牌验证] 服务名不匹配，期望: %s, 实际: %s, 路径: %s", serviceName, claims.ServiceName, r.URL.Path)
				http.Error(w, utils.SERVICE_NAME_MISMATCH, http.StatusUnauthorized)
				return
			}

			log.Printf("[内部令牌验证] 验证成功，用户ID: %d, 服务: %s, 路径: %s", claims.UserID, claims.ServiceName, r.URL.Path)
			// 令牌验证成功，继续处理请求
			next(w, r)
		}
	}
}
