package keys

// contextKey 用户上下文键类型，避免与其他包写入 context 的键冲突
type contextKey string

const (
	UserIDKey        = contextKey("user_id")
	UsernameKey      = contextKey("username")
	SessionIDKey     = contextKey("session_id")
	TokenKey         = contextKey("token")
	InternalTokenKey = contextKey("internal_token")
)
