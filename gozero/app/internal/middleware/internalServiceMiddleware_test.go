package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"app/common/testkit"
	"app/common/utils"
)

// 创建测试用的内部令牌工具实例
func newTestInternalTokenUtil(t *testing.T) *utils.InternalTokenUtil {
	t.Helper()
	tokenUtil, err := utils.NewInternalTokenUtil("middleware-unit-test-secret", 60000)
	if err != nil {
		t.Fatalf("创建内部令牌工具失败: %v", err)
	}
	return tokenUtil
}

// 使用指定工具生成测试用内部令牌
func generateInternalToken(t *testing.T, tokenUtil *utils.InternalTokenUtil, serviceName string) string {
	t.Helper()
	token, err := tokenUtil.GenerateInternalToken(42, serviceName)
	if err != nil {
		t.Fatalf("生成内部令牌失败: %v", err)
	}
	return token
}

// 验证该测试场景的预期行为

func TestInternalServiceMiddlewareRejectsMissingToken(t *testing.T) {
	tokenUtil := newTestInternalTokenUtil(t)
	recorder := httptest.NewRecorder()
	called := false
	handler := NewInternalServiceMiddleware(testkit.NewTestLogger(t), tokenUtil).Handle(func(http.ResponseWriter, *http.Request) {
		called = true
	})
	handler(recorder, httptest.NewRequest(http.MethodGet, "/internal", nil))
	if recorder.Code != http.StatusUnauthorized || called {
		t.Fatalf("状态码 = %d, called = %v", recorder.Code, called)
	}
}

// 验证该测试场景的预期行为

func TestInternalServiceMiddlewareAcceptsValidToken(t *testing.T) {
	tokenUtil := newTestInternalTokenUtil(t)
	token := generateInternalToken(t, tokenUtil, "gozero")
	recorder := httptest.NewRecorder()
	called := false
	internal := NewInternalServiceMiddleware(testkit.NewTestLogger(t), tokenUtil).Handle(func(http.ResponseWriter, *http.Request) {
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
	tokenUtil := newTestInternalTokenUtil(t)
	token := generateInternalToken(t, tokenUtil, "gozero")
	recorder := httptest.NewRecorder()
	called := false
	internal := NewInternalTokenMiddleware(testkit.NewTestLogger(t), tokenUtil, "spring")(func(http.ResponseWriter, *http.Request) {
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

// 验证该测试场景的预期行为

func TestInternalServiceMiddlewareRejectsUninitializedTokenUtil(t *testing.T) {
	tokenUtil := newTestInternalTokenUtil(t)
	token := generateInternalToken(t, tokenUtil, "gozero")
	recorder := httptest.NewRecorder()
	called := false
	// 未注入令牌工具时应拒绝校验而不是放行
	handler := NewInternalServiceMiddleware(testkit.NewTestLogger(t), nil).Handle(func(http.ResponseWriter, *http.Request) {
		called = true
	})
	request := httptest.NewRequest(http.MethodGet, "/internal", nil)
	request.Header.Set("X-Internal-Token", "Bearer "+token)
	handler(recorder, request)
	if recorder.Code != http.StatusUnauthorized || called {
		t.Fatalf("状态码 = %d, called = %v", recorder.Code, called)
	}
}
