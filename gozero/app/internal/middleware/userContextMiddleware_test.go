package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"app/common/keys"
)

func TestUserContextMiddleware(t *testing.T) {
	request := httptest.NewRequest(http.MethodGet, "/test", nil)
	request.Header.Set("X-User-Id", "42")
	request.Header.Set("X-Username", "tester")
	request.Header.Set("X-Session-Id", "session-1")
	request.Header.Set("Authorization", "Bearer access-token")
	request.Header.Set("X-Internal-Token", "Bearer internal-token")

	called := false
	handler := NewUserContextMiddleware().Handle(func(_ http.ResponseWriter, r *http.Request) {
		called = true
		assertContextValue(t, r, keys.UserIDKey, int64(42))
		assertContextValue(t, r, keys.UsernameKey, "tester")
		assertContextValue(t, r, keys.SessionIDKey, "session-1")
		assertContextValue(t, r, keys.TokenKey, "access-token")
		assertContextValue(t, r, keys.InternalTokenKey, "internal-token")
	})
	handler(httptest.NewRecorder(), request)
	if !called {
		t.Fatal("后续 handler 未执行")
	}
}

func TestUserContextMiddlewareInvalidUserID(t *testing.T) {
	request := httptest.NewRequest(http.MethodGet, "/test", nil)
	request.Header.Set("X-User-Id", "invalid")

	NewUserContextMiddleware().Handle(func(_ http.ResponseWriter, r *http.Request) {
		assertContextValue(t, r, keys.UserIDKey, int64(0))
	})(httptest.NewRecorder(), request)
}

func TestExtractBearerToken(t *testing.T) {
	tests := []struct {
		header string
		want   string
	}{
		{header: "Bearer token", want: "token"},
		{header: "Bearer "},
		{header: "bearer token"},
		{header: "token"},
	}
	for _, test := range tests {
		if got := extractBearerToken(test.header); got != test.want {
			t.Errorf("extractBearerToken(%q) = %q, want %q", test.header, got, test.want)
		}
	}
}

func assertContextValue[T comparable](t *testing.T, r *http.Request, key any, want T) {
	t.Helper()
	got, ok := r.Context().Value(key).(T)
	if !ok || got != want {
		t.Fatalf("上下文值 = %v, want %v", got, want)
	}
}
