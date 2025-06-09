package ctxkey

type contextKey string

const UserIDKey = contextKey("user_id")
const UsernameKey = contextKey("username")
