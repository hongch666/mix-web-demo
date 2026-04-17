package middleware

import (
	"fmt"
	"net/http"
	"strings"
	"time"

	"app/common/utils"
)

const (
	InternalTokenHeader = "X-Internal-Token"
	BearerPrefix        = "Bearer "
)

type InternalServiceMiddleware struct {
	*utils.ZeroLogger
}

func NewInternalServiceMiddleware(log *utils.ZeroLogger) *InternalServiceMiddleware {
	return &InternalServiceMiddleware{ZeroLogger: log}
}

// Handle 处理内部服务令牌验证
// serviceName 为空表示不验证服务名称
func (m *InternalServiceMiddleware) Handle(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// 从请求头中提取内部令牌
		authHeader := r.Header.Get(InternalTokenHeader)
		if authHeader == "" {
			m.Error(fmt.Sprintf(utils.INTERNAL_TOKEN_HEADER_MISSING_LOG, InternalTokenHeader, r.URL.Path))
			utils.Error(w, utils.INTERNAL_TOKEN_MISSING)
			return
		}

		// 移除 Bearer 前缀
		tokenString := authHeader
		if strings.HasPrefix(authHeader, BearerPrefix) {
			tokenString = authHeader[len(BearerPrefix):]
		}

		if tokenString == "" {
			m.Error(fmt.Sprintf(utils.INTERNAL_TOKEN_EMPTY_LOG, r.URL.Path))
			utils.Error(w, utils.INTERNAL_TOKEN_MISSING)
			return
		}

		// 验证令牌
		tokenUtil := utils.GetTokenUtil()
		claims, err := tokenUtil.ValidateInternalToken(tokenString)
		if err != nil {
			m.Error(fmt.Sprintf(utils.INTERNAL_TOKEN_VALIDATE_FAIL_LOG, err, r.URL.Path))
			utils.Error(w, utils.INTERNAL_TOKEN_INVALID)
			return
		}

		// 检查令牌是否过期
		if claims.ExpiresAt != nil && claims.ExpiresAt.Before(time.Now()) {
			m.Error(fmt.Sprintf(utils.INTERNAL_TOKEN_EXPIRED_LOG, r.URL.Path))
			utils.Error(w, utils.INTERNAL_TOKEN_EXPIRED)
			return
		}

		m.Info(fmt.Sprintf(utils.INTERNAL_TOKEN_VALIDATE_SUCCESS_LOG, claims.UserID, claims.ServiceName, r.URL.Path))
		// 令牌验证成功，继续处理请求
		next(w, r)
	}
}

// NewInternalTokenMiddleware 创建需要验证特定服务的中间件
func NewInternalTokenMiddleware(log *utils.ZeroLogger, serviceName string) func(http.HandlerFunc) http.HandlerFunc {
	m := &InternalServiceMiddleware{ZeroLogger: log}
	return func(next http.HandlerFunc) http.HandlerFunc {
		return func(w http.ResponseWriter, r *http.Request) {
			// 从请求头中提取内部令牌
			authHeader := r.Header.Get(InternalTokenHeader)
			if authHeader == "" {
				m.Error(fmt.Sprintf(utils.INTERNAL_TOKEN_HEADER_MISSING_LOG, InternalTokenHeader, r.URL.Path))
				utils.Error(w, utils.INTERNAL_TOKEN_MISSING)
				return
			}

			// 移除 Bearer 前缀
			tokenString := authHeader
			if strings.HasPrefix(authHeader, BearerPrefix) {
				tokenString = authHeader[len(BearerPrefix):]
			}

			if tokenString == "" {
				m.Error(fmt.Sprintf(utils.INTERNAL_TOKEN_EMPTY_LOG, r.URL.Path))
				utils.Error(w, utils.INTERNAL_TOKEN_MISSING)
				return
			}

			// 验证令牌
			tokenUtil := utils.GetTokenUtil()
			claims, err := tokenUtil.ValidateInternalToken(tokenString)
			if err != nil {
				m.Error(fmt.Sprintf(utils.INTERNAL_TOKEN_VALIDATE_FAIL_LOG, err, r.URL.Path))
				utils.Error(w, utils.INTERNAL_TOKEN_INVALID)
				return
			}

			// 检查令牌是否过期
			if claims.ExpiresAt != nil && claims.ExpiresAt.Before(time.Now()) {
				m.Error(fmt.Sprintf(utils.INTERNAL_TOKEN_EXPIRED_LOG, r.URL.Path))
				utils.Error(w, utils.INTERNAL_TOKEN_EXPIRED)
				return
			}

			// 验证服务名称（如果指定了）
			if serviceName != "" && claims.ServiceName != serviceName {
				m.Error(fmt.Sprintf(utils.INTERNAL_TOKEN_SERVICE_MISMATCH_LOG, serviceName, claims.ServiceName, r.URL.Path))
				utils.Error(w, utils.SERVICE_NAME_MISMATCH)
				return
			}

			m.Info(fmt.Sprintf(utils.INTERNAL_TOKEN_VALIDATE_SUCCESS_LOG, claims.UserID, claims.ServiceName, r.URL.Path))
			// 令牌验证成功，继续处理请求
			next(w, r)
		}
	}
}
