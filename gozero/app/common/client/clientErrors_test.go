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

type timeoutErr struct{}

func (timeoutErr) Error() string { return "i/o timeout" }

func (timeoutErr) Timeout() bool { return true }

func TestShouldRetry(t *testing.T) {
	dialRefused := &net.OpError{
		Op:  opDial,
		Net: "tcp",
		Err: errors.New("connection refused"),
	}
	readReset := &net.OpError{
		Op:  "read",
		Net: "tcp",
		Err: errors.New("connection reset by peer"),
	}

	tests := []struct {
		name string
		err  error
		want bool
	}{
		{name: "空错误", err: nil, want: false},
		{name: "下游500", err: newHTTPStatusError(constants.HttpInternalServerError, "boom"), want: true},
		{name: "下游503", err: newHTTPStatusError(constants.HttpServiceUnavailable, "boom"), want: true},
		{name: "包装后的502", err: fmt.Errorf("远程调用失败: %w", newHTTPStatusError(constants.HttpBadGateway, "boom")), want: true},
		{name: "下游404", err: newHTTPStatusError(404, "not found"), want: false},
		{name: "下游400", err: newHTTPStatusError(constants.HttpBadRequest, "bad request"), want: false},
		{name: "业务错误", err: fmt.Errorf(constants.SERVICE_CALL_FAILED, "参数错误"), want: false},
		{name: "仅文案类似状态错误", err: fmt.Errorf(constants.UNEXPECTED_STATUS_CODE, 500, "x"), want: false},
		{name: "仅文案包含拒绝连接", err: errors.New("connect: connection refused"), want: false},
		{name: "拨号被拒绝", err: dialRefused, want: true},
		{name: "拨号超时", err: &net.OpError{Op: opDial, Net: "tcp", Err: timeoutErr{}}, want: true},
		{name: "读取连接被重置", err: readReset, want: false},
		{name: "调用方取消", err: context.Canceled, want: true},
		{name: "上下文超时", err: context.DeadlineExceeded, want: true},
		{name: "响应体截断", err: io.ErrUnexpectedEOF, want: true},
		{name: "读取到EOF", err: io.EOF, want: true},
		{name: "连接已关闭", err: net.ErrClosed, want: true},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			if got := shouldRetry(test.err); got != test.want {
				t.Errorf("shouldRetry(%v) = %v, 期望 %v", test.err, got, test.want)
			}
		})
	}
}

func TestHTTPStatusErrorFields(t *testing.T) {
	err := newHTTPStatusError(constants.HttpServiceUnavailable, "服务暂不可用")

	var statusErr *httpStatusError
	if !errors.As(err, &statusErr) {
		t.Fatal("errors.As 未能识别 httpStatusError")
	}
	if statusErr.StatusCode != constants.HttpServiceUnavailable {
		t.Errorf("StatusCode = %d, 期望 %d", statusErr.StatusCode, constants.HttpServiceUnavailable)
	}

	want := fmt.Sprintf(constants.UNEXPECTED_STATUS_CODE, constants.HttpServiceUnavailable, "服务暂不可用")
	if err.Error() != want {
		t.Errorf("Error() = %q, 期望 %q", err.Error(), want)
	}
}
