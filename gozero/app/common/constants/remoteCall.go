package constants

// ===== 远程调用协议常量 =====

const (
	// ===== 远程调用协议 =====

	// RemoteBreakerNamePrefix 远程调用熔断器名称前缀，与 httpc 内部熔断器命名保持一致
	// 远程调用熔断器名称前缀，与 httpc 内部命名一致
	RemoteBreakerNamePrefix = "remote-http:"
	// InternalTokenServiceName 内部令牌中标识调用方服务名
	// 内部令牌中标识本服务的名称
	InternalTokenServiceName = "gozero"
	// BearerPrefix 认证请求头取值前缀
	// 认证请求头取值的鉴权前缀
	BearerPrefix = "Bearer "
)

// ===== 远程调用与用户上下文请求头，出站注入与入站解析共用同一来源 =====

const (
	// ===== 请求头名称 =====

	// 用户 ID 请求头
	HeaderUserID = "X-User-Id"
	// 用户名请求头
	HeaderUsername = "X-Username"
	// 会话 ID 请求头
	HeaderSessionID = "X-Session-Id"
	// 认证请求头
	HeaderAuthorization = "Authorization"
	// 内部服务令牌请求头
	HeaderInternalToken = "X-Internal-Token"
	// 请求体类型请求头
	HeaderContentType = "Content-Type"
)
