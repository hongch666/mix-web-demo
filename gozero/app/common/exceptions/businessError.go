package exceptions

import "app/common/utils"

// BusinessError 业务异常结构体 - 用于返回可向客户端显示的错误信息
// 其他未捕获的异常会统一返回 "服务器内部错误"
type BusinessError struct {
	Code    int    // HTTP 状态码
	Message string // 返回给客户端的错误信息
	Err     string // 实际的错误信息（用于后台日志记录）
}

// NewBusinessError 创建新的业务异常
func NewBusinessError(code int, message string, err string) *BusinessError {
	return &BusinessError{
		Code:    code,
		Message: message,
		Err:     err,
	}
}

// NewBusinessErrorSame 创建新的业务异常(相同消息和错误)
func NewBusinessErrorSame(code int, message string) *BusinessError {
	return &BusinessError{
		Code:    code,
		Message: message,
		Err:     message,
	}
}

// Error 实现 error 接口
func (e *BusinessError) Error() string {
	return e.Message
}

// BusinessCode 返回业务错误的 HTTP 状态码
func (e *BusinessError) BusinessCode() int {
	return e.Code
}

// BusinessMessage 返回业务错误的客户端消息
func (e *BusinessError) BusinessMessage() string {
	return e.Message
}

// IsBusinessError 判断 error 是否为 BusinessError 类型
func IsBusinessError(err error) (*BusinessError, bool) {
	if be, ok := err.(*BusinessError); ok {
		return be, true
	}
	return nil, false
}

// NewBadRequestError 创建 400 Bad Request 业务异常
func NewBadRequestError(message string, err string) *BusinessError {
	return NewBusinessError(utils.HttpBadRequest, message, err)
}

// NewBadRequestErrorSame 创建 400 Bad Request 业务异常(相同消息和错误)
func NewBadRequestErrorSame(message string) *BusinessError {
	return NewBusinessErrorSame(utils.HttpBadRequest, message)
}

// NewUnauthorizedError 创建 401 Unauthorized 业务异常
func NewUnauthorizedError(message string, err string) *BusinessError {
	return NewBusinessError(utils.HttpUnauthorized, message, err)
}

// NewUnauthorizedErrorSame 创建 401 Unauthorized 业务异常(相同消息和错误)
func NewUnauthorizedErrorSame(message string) *BusinessError {
	return NewBusinessErrorSame(utils.HttpUnauthorized, message)
}

// NewForbiddenError 创建 403 Forbidden 业务异常
func NewForbiddenError(message string, err string) *BusinessError {
	return NewBusinessError(utils.HttpForbidden, message, err)
}

// NewForbiddenErrorSame 创建 403 Forbidden 业务异常(相同消息和错误)
func NewForbiddenErrorSame(message string) *BusinessError {
	return NewBusinessErrorSame(utils.HttpForbidden, message)
}

// NewInternalServerError 创建 500 Internal Server Error 业务异常
func NewInternalServerError(message string, err string) *BusinessError {
	return NewBusinessError(utils.HttpInternalServerError, message, err)
}

// NewInternalServerErrorSame 创建 500 Internal Server Error 业务异常(相同消息和错误)
func NewInternalServerErrorSame(message string) *BusinessError {
	return NewBusinessErrorSame(utils.HttpInternalServerError, message)
}

// NewBadGatewayError 创建 502 Bad Gateway 业务异常
func NewBadGatewayError(message string, err string) *BusinessError {
	return NewBusinessError(utils.HttpBadGateway, message, err)
}

// NewBadGatewayErrorSame 创建 502 Bad Gateway 业务异常(相同消息和错误)
func NewBadGatewayErrorSame(message string) *BusinessError {
	return NewBusinessErrorSame(utils.HttpBadGateway, message)
}

// NewServiceUnavailableError 创建 503 Service Unavailable 业务异常
func NewServiceUnavailableError(message string, err string) *BusinessError {
	return NewBusinessError(utils.HttpServiceUnavailable, message, err)
}

// NewServiceUnavailableErrorSame 创建 503 Service Unavailable 业务异常(相同消息和错误)
func NewServiceUnavailableErrorSame(message string) *BusinessError {
	return NewBusinessErrorSame(utils.HttpServiceUnavailable, message)
}
