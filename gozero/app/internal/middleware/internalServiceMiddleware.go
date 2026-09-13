package middleware

import (
	"fmt"
	"net/http"
	"time"

	"app/common/constants"
	"app/common/keys"
	"app/common/utils"
)

const (
	InternalTokenHeader = "X-Internal-Token"
)

type InternalServiceMiddleware struct {
	*utils.ZeroLogger
}

func NewInternalServiceMiddleware(log *utils.ZeroLogger) *InternalServiceMiddleware {
	return &InternalServiceMiddleware{ZeroLogger: log}
}

// validateInternalToken 从上下文中提取并校验内部令牌（公共逻辑）
// 返回 claims、错误响应是否已发送、是否应该继续处理
func validateInternalToken(
	w http.ResponseWriter,
	r *http.Request,
	m *InternalServiceMiddleware,
	expectedServiceName string,
) (shouldContinue bool) {
	// 从上下文中获取已解析的内部令牌（由 UserContextMiddleware 预先解析）
	tokenString, _ := r.Context().Value(keys.InternalTokenKey).(string)
	if tokenString == "" {
		m.Error(fmt.Sprintf(constants.INTERNAL_TOKEN_HEADER_MISSING_LOG, InternalTokenHeader, r.URL.Path))
		utils.Error(w, constants.HttpUnauthorized, constants.INTERNAL_TOKEN_MISSING)
		return false
	}

	// 验证令牌
	tokenUtil, err := utils.GetTokenUtil()
	if err != nil {
		m.Error(fmt.Sprintf(constants.INTERNAL_TOKEN_VALIDATE_FAIL_LOG, err, r.URL.Path))
		utils.Error(w, constants.HttpUnauthorized, constants.INTERNAL_TOKEN_INVALID)
		return false
	}
	claims, err := tokenUtil.ValidateInternalToken(tokenString)
	if err != nil {
		m.Error(fmt.Sprintf(constants.INTERNAL_TOKEN_VALIDATE_FAIL_LOG, err, r.URL.Path))
		utils.Error(w, constants.HttpUnauthorized, constants.INTERNAL_TOKEN_INVALID)
		return false
	}

	// 检查令牌是否过期
	if claims.ExpiresAt != nil && claims.ExpiresAt.Before(time.Now()) {
		m.Error(fmt.Sprintf(constants.INTERNAL_TOKEN_EXPIRED_LOG, r.URL.Path))
		utils.Error(w, constants.HttpUnauthorized, constants.INTERNAL_TOKEN_EXPIRED)
		return false
	}

	// 验证服务名称（如果指定了）
	if expectedServiceName != "" && claims.ServiceName != expectedServiceName {
		m.Error(fmt.Sprintf(constants.INTERNAL_TOKEN_SERVICE_MISMATCH_LOG, expectedServiceName, claims.ServiceName, r.URL.Path))
		utils.Error(w, constants.HttpForbidden, constants.SERVICE_NAME_MISMATCH)
		return false
	}

	m.Info(fmt.Sprintf(constants.INTERNAL_TOKEN_VALIDATE_SUCCESS_LOG, claims.UserID, claims.ServiceName, r.URL.Path))
	return true
}

// Handle 处理内部服务令牌验证（不校验服务名称）
// serviceName 为空表示不验证服务名称
func (m *InternalServiceMiddleware) Handle(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if !validateInternalToken(w, r, m, "") {
			return
		}
		next(w, r)
	}
}

// NewInternalTokenMiddleware 创建需要验证特定服务的中间件
func NewInternalTokenMiddleware(log *utils.ZeroLogger, serviceName string) func(http.HandlerFunc) http.HandlerFunc {
	m := &InternalServiceMiddleware{ZeroLogger: log}
	return func(next http.HandlerFunc) http.HandlerFunc {
		return func(w http.ResponseWriter, r *http.Request) {
			if !validateInternalToken(w, r, m, serviceName) {
				return
			}
			next(w, r)
		}
	}
}
