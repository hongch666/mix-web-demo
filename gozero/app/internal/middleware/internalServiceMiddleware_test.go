package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"app/common/utils"
)

// 验证该测试场景的预期行为

func TestInternalServiceMiddlewareRejectsMissingToken(t *testing.T) {
	recorder := httptest.NewRecorder()
	called := false
	handler := NewInternalServiceMiddleware(newMiddlewareTestLogger(t)).Handle(func(http.ResponseWriter, *http.Request) {
		called = true
	})
	handler(recorder, httptest.NewRequest(http.MethodGet, "/internal", nil))
	if recorder.Code != http.StatusUnauthorized || called {
		t.Fatalf("状态码 = %d, called = %v", recorder.Code, called)
	}
}

// 验证该测试场景的预期行为

func TestInternalServiceMiddlewareAcceptsValidToken(t *testing.T) {
	token := generateInternalToken(t, "gozero")
	recorder := httptest.NewRecorder()
	called := false
	internal := NewInternalServiceMiddleware(newMiddlewareTestLogger(t)).Handle(func(http.ResponseWriter, *http.Request) {
		called = true
	})
	handler := NewUserContextMiddleware().Handle(internal)
	request := httptest.NewRequest(http.MethodGet, "/internal", nil)
	request.Header.Set("X-Internal-Token", "Bearer "+token)
	handler(recorder, request)
	if recorder.Code != http.StatusOK || !called {
		t.Fatalf("状态码 = %d, called = %v", recorder.Code, called)
	}
}

// 验证该测试场景的预期行为

func TestInternalServiceMiddlewareRejectsServiceMismatch(t *testing.T) {
	token := generateInternalToken(t, "gozero")
	recorder := httptest.NewRecorder()
	called := false
	internal := NewInternalTokenMiddleware(newMiddlewareTestLogger(t), "spring")(func(http.ResponseWriter, *http.Request) {
		called = true
	})
	handler := NewUserContextMiddleware().Handle(internal)
	request := httptest.NewRequest(http.MethodGet, "/internal", nil)
	request.Header.Set("X-Internal-Token", "Bearer "+token)
	handler(recorder, request)
	if recorder.Code != http.StatusForbidden || called {
		t.Fatalf("状态码 = %d, called = %v", recorder.Code, called)
	}
}

func generateInternalToken(t *testing.T, serviceName string) string {
	t.Helper()
	if err := utils.InitInternalTokenUtil("middleware-unit-test-secret", 60000); err != nil {
		t.Fatalf("初始化内部令牌工具失败: %v", err)
	}
	tokenUtil, err := utils.GetTokenUtil()
	if err != nil {
		t.Fatalf("获取内部令牌工具失败: %v", err)
	}
	token, err := tokenUtil.GenerateInternalToken(42, serviceName)
	if err != nil {
		t.Fatalf("生成内部令牌失败: %v", err)
	}
	return token
}
