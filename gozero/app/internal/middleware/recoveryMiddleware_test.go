package middleware

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"app/common/constants"
	"app/common/exceptions"
)

func TestRecoveryMiddlewarePassesThrough(t *testing.T) {
	recorder := httptest.NewRecorder()
	handler := NewRecoveryMiddleware(newMiddlewareTestLogger(t)).Handle(func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusNoContent)
	})
	handler(recorder, httptest.NewRequest(http.MethodGet, "/test", nil))
	if recorder.Code != http.StatusNoContent {
		t.Fatalf("状态码 = %d, want %d", recorder.Code, http.StatusNoContent)
	}
}

func TestRecoveryMiddlewareHandlesBusinessPanic(t *testing.T) {
	recorder := httptest.NewRecorder()
	handler := NewRecoveryMiddleware(newMiddlewareTestLogger(t)).Handle(func(http.ResponseWriter, *http.Request) {
		panic(exceptions.NewForbiddenErrorSame("禁止访问"))
	})
	handler(recorder, httptest.NewRequest(http.MethodGet, "/test", nil))
	if recorder.Code != http.StatusForbidden || !strings.Contains(recorder.Body.String(), "禁止访问") {
		t.Fatalf("响应 = %d %s", recorder.Code, recorder.Body.String())
	}
}

func TestRecoveryMiddlewareHandlesUnknownPanic(t *testing.T) {
	recorder := httptest.NewRecorder()
	handler := NewRecoveryMiddleware(newMiddlewareTestLogger(t)).Handle(func(http.ResponseWriter, *http.Request) {
		panic("unexpected")
	})
	handler(recorder, httptest.NewRequest(http.MethodGet, "/test", nil))
	if recorder.Code != http.StatusInternalServerError ||
		!strings.Contains(recorder.Body.String(), constants.UNIFIED_ERROR_RESPONSE_MESSAGE) {
		t.Fatalf("响应 = %d %s", recorder.Code, recorder.Body.String())
	}
}
