package utils

// HTTP 状态码常量 - 与 HTTP 响应状态码一致，同时作为响应体中的 code 字段值
const (
	HttpOK                  = 200
	HttpMultipleChoices     = 300
	HttpBadRequest          = 400
	HttpUnauthorized        = 401
	HttpForbidden           = 403
	HttpInternalServerError = 500
	HttpBadGateway          = 502
	HttpServiceUnavailable  = 503
)
