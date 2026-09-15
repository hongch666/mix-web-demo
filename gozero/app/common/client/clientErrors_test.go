package client

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"testing"

	"app/common/constants"
)

// timeoutErr 模拟仅暴露 Timeout 语义的网络错误
type timeoutErr struct{}

func (timeoutErr) Error() string { return "i/o timeout" }

func (timeoutErr) Timeout() bool { return true }

func TestShouldRetry(t *testing.T) {
	dialRefused := &net.OpError{
		Op:  opDial,
		Net: "tcp",
		Err: errors.New("connectex: 目标计算机积极拒绝，无法连接"),
	}
	readReset := &net.OpError{
		Op:  "read",
		Net: "tcp",
		Err: errors.New("connection reset by peer"),
	}

	cases := []struct {
		name string
		err  error
		want bool
	}{
		{"空错误", nil, false},
		{"下游 500", newHTTPStatusError(constants.HttpInternalServerError, "boom"), true},
		{"下游 503", newHTTPStatusError(constants.HttpServiceUnavailable, "boom"), true},
		{"下游 502 经包装仍可识别", fmt.Errorf("远程调用失败: %w", newHTTPStatusError(constants.HttpBadGateway, "boom")), true},
		{"下游 404", newHTTPStatusError(404, "not found"), false},
		{"下游 400", newHTTPStatusError(constants.HttpBadRequest, "bad request"), false},
		{"业务错误", fmt.Errorf(constants.SERVICE_CALL_FAILED, "参数错误"), false},
		{"文案相同但类型不符的错误", fmt.Errorf(constants.UNEXPECTED_STATUS_CODE, 500, "x"), false},
		{"文案含 connection refused 的普通错误", errors.New("connect: connection refused"), false},
		{"拨号被拒", dialRefused, true},
		{"拨号超时", &net.OpError{Op: opDial, Net: "tcp", Err: timeoutErr{}}, true},
		{"读连接被重置", readReset, false},
		{"调用方取消", context.Canceled, true},
		{"上下文超时", context.DeadlineExceeded, true},
		{"响应体截断", io.ErrUnexpectedEOF, true},
		{"读到 EOF", io.EOF, true},
		{"连接已关闭", net.ErrClosed, true},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := shouldRetry(tc.err); got != tc.want {
				t.Errorf("shouldRetry(%v) = %v, 期望 %v", tc.err, got, tc.want)
			}
		})
	}
}

func TestHTTPStatusErrorFields(t *testing.T) {
	err := newHTTPStatusError(constants.HttpServiceUnavailable, "服务暂不可用")

	var statusErr *httpStatusError
	if !errors.As(err, &statusErr) {
		t.Fatalf("errors.As 未能识别 httpStatusError")
	}
	if statusErr.StatusCode != constants.HttpServiceUnavailable {
		t.Errorf("StatusCode = %d, 期望 %d", statusErr.StatusCode, constants.HttpServiceUnavailable)
	}

	want := fmt.Sprintf(constants.UNEXPECTED_STATUS_CODE, constants.HttpServiceUnavailable, "服务暂不可用")
	if err.Error() != want {
		t.Errorf("Error() = %q, 期望 %q", err.Error(), want)
	}
}

// TestShouldRetryRealDialError 用真实拨号失败校验判定，覆盖底层错误链的实际形态
func TestShouldRetryRealDialError(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Skipf("无法创建监听套接字: %v", err)
	}
	addr := listener.Addr().String()
	if err := listener.Close(); err != nil {
		t.Skipf("关闭监听套接字失败: %v", err)
	}

	_, dialErr := (&net.Dialer{}).DialContext(context.Background(), "tcp", addr)
	if dialErr == nil {
		t.Skip("端口未按预期拒绝连接")
	}
	if !shouldRetry(dialErr) {
		t.Errorf("真实拨号失败应可重试, err = %v", dialErr)
	}
}
