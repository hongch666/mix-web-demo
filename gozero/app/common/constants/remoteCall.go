package constants

// 远程调用协议常量
const (
	// RemoteBreakerNamePrefix 远程调用熔断器名称前缀，与 httpc 内部熔断器命名保持一致
	RemoteBreakerNamePrefix = "remote-http:"
	// InternalTokenServiceName 内部令牌中标识调用方服务名
	InternalTokenServiceName = "gozero"
	// BearerPrefix 认证请求头取值前缀
	BearerPrefix = "Bearer "
)

// 远程调用与用户上下文请求头，出站注入与入站解析共用同一来源
const (
	HeaderUserID        = "X-User-Id"
	HeaderUsername      = "X-Username"
	HeaderSessionID     = "X-Session-Id"
	HeaderAuthorization = "Authorization"
	HeaderInternalToken = "X-Internal-Token"
	HeaderContentType   = "Content-Type"
)
