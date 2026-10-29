package constants

// ===== HTTP 状态码常量 - 与 HTTP 响应状态码一致，同时作为响应体中的 code 字段值 =====

const (
	// 请求成功
	HttpOK = 200
	// 资源存在多个可选地址
	HttpMultipleChoices = 300
	// 参数或请求体不合法
	HttpBadRequest = 400
	// 未认证或令牌失效
	HttpUnauthorized = 401
	// 已认证但无权限
	HttpForbidden = 403
	// 服务内部异常
	HttpInternalServerError = 500
	// 下游服务返回异常
	HttpBadGateway = 502
	// 依赖缺失导致服务不可用
	HttpServiceUnavailable = 503
)
