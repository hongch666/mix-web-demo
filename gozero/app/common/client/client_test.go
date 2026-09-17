package client

import (
	"context"
	"encoding/json"
	"errors"
	"net"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strconv"
	"sync/atomic"
	"testing"
	"time"

	"app/common/keys"
	"app/common/utils"

	"github.com/nacos-group/nacos-sdk-go/v2/model"
)

func TestCallWithRetryPropagatesContextHeadersAndInternalToken(t *testing.T) {
	if err := utils.InitInternalTokenUtil("unit-test-secret-unit-test-secret", 60000); err != nil {
		t.Fatalf("初始化内部令牌失败: %v", err)
	}
	var captured http.Header
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		captured = r.Header.Clone()
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(Result{Code: http.StatusOK, Msg: "ok", Data: map[string]any{"id": 1}})
	}))
	defer server.Close()
	sd := newTestServiceDiscovery(t, server, 1)
	ctx := context.WithValue(context.Background(), keys.UserIDKey, int64(7))
	ctx = context.WithValue(ctx, keys.UsernameKey, "alice")
	ctx = context.WithValue(ctx, keys.SessionIDKey, "session-1")
	ctx = context.WithValue(ctx, keys.TokenKey, "access-token")

	result, err := sd.callWithRetry(ctx, "spring", "/resource", RequestOptions{
		Method:  http.MethodGet,
		Headers: map[string]string{"X-Custom": "custom"},
	})
	if err != nil {
		t.Fatalf("远程调用失败: %v", err)
	}
	if result.Code != http.StatusOK {
		t.Fatalf("响应码 = %d, 期望 200", result.Code)
	}
	if captured.Get("X-User-Id") != "7" || captured.Get("X-Username") != "alice" || captured.Get("X-Session-Id") != "session-1" {
		t.Fatalf("用户上下文请求头错误: %+v", captured)
	}
	if captured.Get("Authorization") != "Bearer access-token" || captured.Get("X-Custom") != "custom" {
		t.Fatalf("认证或自定义请求头错误: %+v", captured)
	}
	claims := parseInternalTokenHeader(t, captured.Get("X-Internal-Token"))
	if claims.UserID != 7 || claims.ServiceName != "gozero" {
		t.Fatalf("内部令牌声明错误: %+v", claims)
	}
}

func TestCallWithRetryUsesSystemIdentityWithoutUserContext(t *testing.T) {
	if err := utils.InitInternalTokenUtil("unit-test-secret-unit-test-secret", 60000); err != nil {
		t.Fatalf("初始化内部令牌失败: %v", err)
	}
	var internalToken string
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		internalToken = r.Header.Get("X-Internal-Token")
		_ = json.NewEncoder(w).Encode(Result{Code: http.StatusOK, Msg: "ok"})
	}))
	defer server.Close()
	sd := newTestServiceDiscovery(t, server, 1)

	if _, err := sd.callWithRetry(context.Background(), "spring", "/resource", RequestOptions{Method: http.MethodGet}); err != nil {
		t.Fatalf("系统调用失败: %v", err)
	}
	claims := parseInternalTokenHeader(t, internalToken)
	if claims.UserID != -1 {
		t.Fatalf("未登录系统调用 userId = %d, 期望 -1", claims.UserID)
	}
}

func TestCallWithRetryRetriesServerErrorThenSucceeds(t *testing.T) {
	var attempts atomic.Int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if attempts.Add(1) < 3 {
			http.Error(w, "temporary", http.StatusServiceUnavailable)
			return
		}
		_ = json.NewEncoder(w).Encode(Result{Code: http.StatusOK, Msg: "ok"})
	}))
	defer server.Close()
	sd := newTestServiceDiscovery(t, server, 3)

	result, err := sd.callWithRetry(context.Background(), "spring", "/resource", RequestOptions{Method: http.MethodGet})
	if err != nil || result.Code != http.StatusOK {
		t.Fatalf("重试后调用失败: result=%+v err=%v", result, err)
	}
	if attempts.Load() != 3 {
		t.Fatalf("调用次数 = %d, 期望 3", attempts.Load())
	}
}

func TestCallWithRetryDoesNotRetryClientError(t *testing.T) {
	var attempts atomic.Int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		attempts.Add(1)
		http.Error(w, "invalid", http.StatusBadRequest)
	}))
	defer server.Close()
	sd := newTestServiceDiscovery(t, server, 3)

	_, err := sd.callWithRetry(context.Background(), "spring", "/resource", RequestOptions{Method: http.MethodGet})
	var statusErr *httpStatusError
	if !errors.As(err, &statusErr) || statusErr.StatusCode != http.StatusBadRequest {
		t.Fatalf("期望 400 类型化错误，实际为 %v", err)
	}
	if attempts.Load() != 1 {
		t.Fatalf("4xx 调用次数 = %d, 期望 1", attempts.Load())
	}
}

func TestCallWithRetryStopsWhenContextIsCanceled(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Fatal("上下文已取消时不应到达服务端")
	}))
	defer server.Close()
	sd := newTestServiceDiscovery(t, server, 3)

	_, err := sd.callWithRetry(ctx, "spring", "/resource", RequestOptions{Method: http.MethodGet})
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("错误 = %v, 期望 context.Canceled", err)
	}
}

func newTestServiceDiscovery(t *testing.T, server *httptest.Server, maxRetries int) *ServiceDiscovery {
	t.Helper()
	parsed, err := url.Parse(server.URL)
	if err != nil {
		t.Fatalf("解析测试服务地址失败: %v", err)
	}
	host, portText, err := net.SplitHostPort(parsed.Host)
	if err != nil {
		t.Fatalf("解析测试服务端口失败: %v", err)
	}
	port, err := strconv.ParseUint(portText, 10, 64)
	if err != nil {
		t.Fatalf("转换测试服务端口失败: %v", err)
	}
	sd := NewServiceDiscovery(nil, RemoteCallConfig{
		Timeout:    time.Second,
		MaxRetries: maxRetries,
	}, nil)
	sd.httpClient = server.Client()
	sd.serviceMap.Store("spring", &serviceCache{
		instances: []model.Instance{{Ip: host, Port: port}},
		timestamp: time.Now(),
	})
	return sd
}

func parseInternalTokenHeader(t *testing.T, header string) *utils.InternalTokenClaims {
	t.Helper()
	const prefix = "Bearer "
	if len(header) <= len(prefix) || header[:len(prefix)] != prefix {
		t.Fatalf("内部令牌请求头格式错误: %q", header)
	}
	tokenUtil, err := utils.GetTokenUtil()
	if err != nil {
		t.Fatalf("获取内部令牌工具失败: %v", err)
	}
	claims, err := tokenUtil.ValidateInternalToken(header[len(prefix):])
	if err != nil {
		t.Fatalf("验证内部令牌失败: %v", err)
	}
	return claims
}
