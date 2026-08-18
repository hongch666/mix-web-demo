package keys

type contextKey string

const (
	UserIDKey        = contextKey("user_id")
	UsernameKey      = contextKey("username")
	SessionIDKey     = contextKey("session_id")
	TokenKey         = contextKey("token")
	InternalTokenKey = contextKey("internal_token")
)
