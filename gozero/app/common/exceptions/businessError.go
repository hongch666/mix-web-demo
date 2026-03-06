package exceptions

// BusinessError 业务异常结构体 - 用于返回可向客户端显示的错误信息
// 其他未捕获的异常会统一返回 "服务器内部错误"
type BusinessError struct {
	Message string // 返回给客户端的错误信息
	Err     string // 实际的错误信息（用于后台日志记录）
}

// NewBusinessError 创建新的业务异常
func NewBusinessError(message string, err string) *BusinessError {
	return &BusinessError{
		Message: message,
		Err:     err,
	}
}

// 创建新的业务异常(相同消息和错误)
func NewBusinessErrorSame(message string) *BusinessError {
	return &BusinessError{
		Message: message,
		Err:     message,
	}
}
