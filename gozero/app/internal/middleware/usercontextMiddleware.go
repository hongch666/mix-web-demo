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

		var userID int64
		if uid, err := strconv.ParseInt(userIDStr, 10, 64); err == nil {
			userID = uid
		}

		// 写入 context
		ctx := context.WithValue(r.Context(), keys.UserIDKey, userID)
		ctx = context.WithValue(ctx, keys.UsernameKey, username)

		// 替换请求上下文
		r = r.WithContext(ctx)

		next(w, r)
	}
}
