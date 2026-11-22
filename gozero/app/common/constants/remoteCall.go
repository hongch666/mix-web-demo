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
	// 内部服务令牌的令牌类型声明值
	InternalTokenType = "internal"
	// 内部服务令牌的 JWT subject 声明值
	InternalTokenSubject = "internal_service_token"
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
	// 缓存控制请求头
	HeaderCacheControl = "Cache-Control"
	// 连接控制请求头
	HeaderConnection = "Connection"
)

// ===== 目标服务名与请求体类型 =====

const (
	// ===== 目标服务名 =====

	// Spring 服务在注册中心的名称
	SpringServiceName = "spring"
	// FastAPI 服务在注册中心的名称
	FastapiServiceName = "fastapi"
	// NestJS 服务在注册中心的名称
	NestjsServiceName = "nestjs"

	// ===== 请求体类型 =====

	// JSON 请求体与消息体的 MIME 类型
	ContentTypeJSON = "application/json"
	// 表单 urlencoded 请求体的 MIME 类型
	ContentTypeFormURLEncoded = "application/x-www-form-urlencoded"
)
