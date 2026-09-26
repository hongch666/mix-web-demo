package middleware

import (
	"context"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"app/common/keys"

	"github.com/zeromicro/go-zero/rest/pathvar"
)

type adminCheckerStub struct {
	isAdmin bool
	err     error
	calls   int
}

func (s *adminCheckerStub) IsAdminUser(context.Context, int64) (bool, error) {
	s.calls++
	return s.isAdmin, s.err
}

// 验证该测试场景的预期行为

func TestRequireSelfOrAdmin(t *testing.T) {
	tests := []struct {
		name      string
		currentID int64
		targetID  int64
		checker   *adminCheckerStub
		wantErr   bool
		wantCalls int
	}{
		{name: "本人直接通过", currentID: 1, targetID: 1, checker: &adminCheckerStub{}},
		{name: "管理员访问他人", currentID: 1, targetID: 2, checker: &adminCheckerStub{isAdmin: true}, wantCalls: 1},
		{name: "普通用户访问他人", currentID: 1, targetID: 2, checker: &adminCheckerStub{}, wantErr: true, wantCalls: 1},
		{name: "缺少登录身份", targetID: 2, checker: &adminCheckerStub{}, wantErr: true},
		{name: "管理员校验失败", currentID: 1, targetID: 2, checker: &adminCheckerStub{err: errors.New("failed")}, wantErr: true, wantCalls: 1},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			ctx := context.WithValue(context.Background(), keys.UserIDKey, test.currentID)
			err := requireSelfOrAdmin(ctx, test.targetID, test.checker)
			if (err != nil) != test.wantErr {
				t.Fatalf("requireSelfOrAdmin() error = %v, wantErr %v", err, test.wantErr)
			}
			if test.checker.calls != test.wantCalls {
				t.Fatalf("管理员校验调用次数 = %d, 期望 %d", test.checker.calls, test.wantCalls)
			}
		})
	}
}

// 验证该测试场景的预期行为

func TestAllowSelfMiddleware(t *testing.T) {
	tests := []struct {
		name       string
		currentID  int64
		targetID   string
		checker    *adminCheckerStub
		wantStatus int
		wantCalled bool
	}{
		{name: "本人访问", currentID: 1, targetID: "1", checker: &adminCheckerStub{}, wantStatus: http.StatusNoContent, wantCalled: true},
		{name: "管理员访问他人", currentID: 1, targetID: "2", checker: &adminCheckerStub{isAdmin: true}, wantStatus: http.StatusNoContent, wantCalled: true},
		{name: "普通用户访问他人", currentID: 1, targetID: "2", checker: &adminCheckerStub{}, wantStatus: http.StatusForbidden},
		{name: "缺少登录身份", targetID: "2", checker: &adminCheckerStub{}, wantStatus: http.StatusUnauthorized},
		{name: "非法目标用户", currentID: 1, targetID: "invalid", checker: &adminCheckerStub{}, wantStatus: http.StatusBadRequest},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			request := httptest.NewRequest(http.MethodGet, "/sse/chat?user_id="+test.targetID, nil)
			request = request.WithContext(context.WithValue(request.Context(), keys.UserIDKey, test.currentID))
			recorder := httptest.NewRecorder()
			called := false
			handler := NewAllowSelfMiddleware(test.checker, newMiddlewareTestLogger(t)).Handle(
				func(w http.ResponseWriter, _ *http.Request) {
					called = true
					w.WriteHeader(http.StatusNoContent)
				},
			)
			handler(recorder, request)
			if recorder.Code != test.wantStatus || called != test.wantCalled {
				t.Fatalf("状态码 = %d, called = %v, wantStatus = %d, wantCalled = %v",
					recorder.Code, called, test.wantStatus, test.wantCalled)
			}
		})
	}
}

// 验证该测试场景的预期行为

func TestResolveTargetUserID(t *testing.T) {
	tests := []struct {
		name      string
		request   func() *http.Request
		currentID int64
		want      int64
		wantErr   bool
	}{
		{
			name: "查询参数用户",
			request: func() *http.Request {
				return httptest.NewRequest("GET", "/sse/chat?user_id=2", nil)
			},
			want: 2,
		},
		{
			name: "路径用户",
			request: func() *http.Request {
				request := httptest.NewRequest("GET", "/search/history/3", nil)
				return pathvar.WithVars(request, map[string]string{"user_id": "3"})
			},
			want: 3,
		},
		{
			name: "请求体用户",
			request: func() *http.Request {
				return httptest.NewRequest("POST", "/user-chat/history", strings.NewReader(`{"user_id":4}`))
			},
			want: 4,
		},
		{
			name: "消息发送者",
			request: func() *http.Request {
				return httptest.NewRequest("POST", "/user-chat/send", strings.NewReader(`{"sender_id":5}`))
			},
			want: 5,
		},
		{
			name: "请求体身份不能被查询参数覆盖",
			request: func() *http.Request {
				return httptest.NewRequest("POST", "/user-chat/send?user_id=1", strings.NewReader(`{"sender_id":5}`))
			},
			want: 5,
		},
		{
			name: "缺省时使用当前用户",
			request: func() *http.Request {
				return httptest.NewRequest("GET", "/ws/chat", nil)
			},
			currentID: 6,
			want:      6,
		},
		{
			name: "非法用户ID",
			request: func() *http.Request {
				return httptest.NewRequest("GET", "/sse/chat?user_id=invalid", nil)
			},
			wantErr: true,
		},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			request := test.request()
			request = request.WithContext(context.WithValue(request.Context(), keys.UserIDKey, test.currentID))
			got, err := resolveTargetUserID(request)
			if (err != nil) != test.wantErr {
				t.Fatalf("resolveTargetUserID() error = %v, wantErr %v", err, test.wantErr)
			}
			if got != test.want {
				t.Fatalf("resolveTargetUserID() = %d, want %d", got, test.want)
			}
		})
	}
}

// 验证该测试场景的预期行为

func TestResolveTargetUserIDRestoresBody(t *testing.T) {
	body := `{"user_id":7,"other_id":8}`
	request := httptest.NewRequest("POST", "/user-chat/history", strings.NewReader(body))

	if _, err := resolveTargetUserID(request); err != nil {
		t.Fatalf("resolveTargetUserID() error = %v", err)
	}
	restored, err := io.ReadAll(request.Body)
	if err != nil {
		t.Fatalf("读取恢复后的请求体失败: %v", err)
	}
	if string(restored) != body {
		t.Fatalf("恢复后的请求体 = %q, want %q", string(restored), body)
	}
}
