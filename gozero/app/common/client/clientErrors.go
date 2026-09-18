package client

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"os"

	"app/common/constants"

	"github.com/zeromicro/go-zero/core/breaker"
)

// opDial net.OpError 中表示拨号操作的值
const opDial = "dial"

// httpStatusError 下游返回非预期 HTTP 状态码的错误
// 用类型携带状态码，使重试判定与错误文案解耦
type httpStatusError struct {
	StatusCode int
	Body       string
}

func (e *httpStatusError) Error() string {
	return fmt.Sprintf(constants.UNEXPECTED_STATUS_CODE, e.StatusCode, e.Body)
}

// newHTTPStatusError 构造 HTTP 状态码错误
func newHTTPStatusError(statusCode int, body string) error {
	return &httpStatusError{
		StatusCode: statusCode,
		Body:       body,
	}
}

// shouldRetry 判断错误是否可重试
// 全部依据错误类型与状态码判定，不匹配错误文案，避免文案调整导致重试静默失效
func shouldRetry(err error) bool {
	if err == nil {
		return false
	}

	// 熔断打开时请求并未发出，重试无意义且会持续冲击熔断器
	if errors.Is(err, breaker.ErrServiceUnavailable) {
		return false
	}

	// 调用方取消或超时
	if errors.Is(err, context.Canceled) || errors.Is(err, context.DeadlineExceeded) {
		return true
	}

	// 下游 5xx 视为服务端暂时性故障，4xx 为请求本身问题不重试
	var statusErr *httpStatusError
	if errors.As(err, &statusErr) {
		return statusErr.StatusCode >= constants.HttpInternalServerError
	}

	// 超时：拨号超时、响应头超时、读超时
	var netErr net.Error
	if errors.As(err, &netErr) && netErr.Timeout() {
		return true
	}
	if errors.Is(err, os.ErrDeadlineExceeded) {
		return true
	}

	// 拨号失败：每次重试都会重新选择服务实例，可换实例重试
	var opErr *net.OpError
	if errors.As(err, &opErr) && opErr.Op == opDial {
		return true
	}

	// 连接中断：响应体读取不完整或连接被关闭
	return errors.Is(err, io.EOF) ||
		errors.Is(err, io.ErrUnexpectedEOF) ||
		errors.Is(err, net.ErrClosed)
}
