package keys

type contextKey string

const (
	UserIDKey   = contextKey("user_id")
	UsernameKey = contextKey("username")
)
