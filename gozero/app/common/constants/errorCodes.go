package constants

// 错误标识类 — 内部令牌、参数校验等错误标识符
const (
	// 内部服务令牌错误标识
	INTERNAL_TOKEN_SECRET_NOT_NULL = "内部服务令牌密钥不能为空"
	INTERNAL_TOKEN_MISSING         = "缺少必需的内部服务令牌请求头"
	INTERNAL_TOKEN_INVALID         = "内部服务令牌无效"
	INTERNAL_TOKEN_EXPIRED         = "内部服务令牌已过期"
	SERVICE_NAME_MISMATCH          = "服务名称不匹配"
)
