package middleware

import (
	"context"
	"net/http"
	"strconv"

	"app/common/keys"
)

type UserContextMiddleware struct{}

func NewUserContextMiddleware() *UserContextMiddleware {
	return &UserContextMiddleware{}
}

// InjectUserContext 注入用户上下文信息
func (m *UserContextMiddleware) Handle(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userIDStr := r.Header.Get("X-User-Id")
		username := r.Header.Get("X-Username")
		sessionID := r.Header.Get("X-Session-Id")
		token := extractBearerToken(r.Header.Get("Authorization"))
		internalToken := extractBearerToken(r.Header.Get("X-Internal-Token"))

		var userID int64
		if uid, err := strconv.ParseInt(userIDStr, 10, 64); err == nil {
			userID = uid
		}

		// 写入 context
		ctx := context.WithValue(r.Context(), keys.UserIDKey, userID)
		ctx = context.WithValue(ctx, keys.UsernameKey, username)
		ctx = context.WithValue(ctx, keys.SessionIDKey, sessionID)
		ctx = context.WithValue(ctx, keys.TokenKey, token)
		ctx = context.WithValue(ctx, keys.InternalTokenKey, internalToken)

		// 替换请求上下文
		r = r.WithContext(ctx)

		next(w, r)
	}
}

// extractBearerToken 从 Authorization 头中提取 Bearer token
func extractBearerToken(header string) string {
	const bearerPrefix = "Bearer "
	if len(header) > len(bearerPrefix) && header[:len(bearerPrefix)] == bearerPrefix {
		return header[len(bearerPrefix):]
	}
	return ""
}
