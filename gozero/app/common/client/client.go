package client

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"

	"app/common/keys"
	"app/common/utils"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
	"github.com/nacos-group/nacos-sdk-go/v2/model"
	"github.com/nacos-group/nacos-sdk-go/v2/vo"
	"github.com/zeromicro/go-zero/core/breaker"
)

const (
	defaultRequestTimeout = 3 * time.Second
	maxRetryAttempts      = 3
	initialRetryBackoff   = 200 * time.Millisecond
	maxRetryBackoff       = 2 * time.Second
)

type ServiceDiscovery struct {
	namingClient naming_client.INamingClient
	serviceMap   sync.Map          // 服务实例缓存
	mu           sync.Mutex        // 保证线程安全
	lbIndex      map[string]uint64 // 负载均衡轮询索引
}

func NewServiceDiscovery(client naming_client.INamingClient) *ServiceDiscovery {
	return &ServiceDiscovery{
		namingClient: client,
		lbIndex:      make(map[string]uint64),
	}
}

// 获取服务实例（带缓存和轮询负载均衡）
func (sd *ServiceDiscovery) GetInstance(serviceName string) (*model.Instance, error) {
	// 1. 查询缓存或从Nacos获取最新实例
	instances, err := sd.getServiceInstances(serviceName)
	if err != nil {
		return nil, err
	}

	// 2. 负载均衡策略（轮询）
	sd.mu.Lock()
	defer sd.mu.Unlock()
	index := sd.lbIndex[serviceName] % uint64(len(instances))
	sd.lbIndex[serviceName]++

	return &instances[index], nil
}

// 定义请求选项结构体
type RequestOptions struct {
	Method      string            // HTTP方法：GET/POST/PUT/DELETE等
	PathParams  map[string]string // 路径参数（如 /users/:id）
	QueryParams url.Values        // URL查询参数
	BodyData    any               // 请求体数据（支持多种格式）
	Headers     map[string]string // 自定义请求头
}

// 定义返回数据结构体
type Result struct {
	Code int    `json:"code"`
	Msg  string `json:"msg"`
	Data any    `json:"data"`
}

// 增强版服务调用方法，始终添加默认请求体字段
func (sd *ServiceDiscovery) CallService(ctx context.Context, serviceName string, path string, opts RequestOptions) (Result, error) {
	var (
		result  Result
		callErr error
	)

	breakerName := "remote-http:" + serviceName
	callErr = breaker.DoWithFallbackAcceptableCtx(ctx, breakerName, func() error {
		var err error
		result, err = sd.callWithRetry(ctx, serviceName, path, opts)
		return err
	}, func(err error) error {
		return fmt.Errorf("下游服务 %s 暂不可用，已触发熔断降级: %w", serviceName, err)
	}, func(err error) bool {
		return err == nil
	})
	if callErr != nil {
		return Result{}, callErr
	}

	return result, nil
}

func (sd *ServiceDiscovery) callWithRetry(ctx context.Context, serviceName string, path string, opts RequestOptions) (Result, error) {
	var lastErr error

	for attempt := 1; attempt <= maxRetryAttempts; attempt++ {
		result, err := sd.doCall(ctx, serviceName, path, opts)
		if err == nil {
			return result, nil
		}

		lastErr = err
		if !shouldRetry(err) || attempt == maxRetryAttempts {
			break
		}

		backoff := calculateBackoff(attempt)
		timer := time.NewTimer(backoff)
		select {
		case <-ctx.Done():
			timer.Stop()
			return Result{}, ctx.Err()
		case <-timer.C:
		}
	}

	return Result{}, lastErr
}

func (sd *ServiceDiscovery) doCall(ctx context.Context, serviceName string, path string, opts RequestOptions) (Result, error) {
	var result Result

	instance, err := sd.GetInstance(serviceName)
	if err != nil {
		return Result{}, err
	}

	baseURL := fmt.Sprintf("http://%s:%d%s", instance.Ip, instance.Port, path)
	if opts.PathParams != nil {
		for key, value := range opts.PathParams {
			baseURL = strings.Replace(baseURL, ":"+key, value, 1)
		}
	}
	if opts.QueryParams != nil {
		baseURL += "?" + opts.QueryParams.Encode()
	}

	bodyBytes, contentType, err := buildRequestBody(opts.BodyData)
	if err != nil {
		return Result{}, err
	}

	attemptCtx, cancel := context.WithTimeout(ctx, defaultRequestTimeout)
	defer cancel()

	var body io.Reader
	if bodyBytes != nil {
		body = bytes.NewReader(bodyBytes)
	}

	req, err := http.NewRequestWithContext(attemptCtx, opts.Method, baseURL, body)
	if err != nil {
		return Result{}, err
	}

	if opts.Headers != nil {
		for k, v := range opts.Headers {
			req.Header.Set(k, v)
		}
	}

	userID, _ := ctx.Value(keys.UserIDKey).(int64)
	username, _ := ctx.Value(keys.UsernameKey).(string)
	req.Header.Set("X-User-Id", fmt.Sprintf("%d", userID))
	req.Header.Set("X-Username", username)

	tokenUtil := utils.GetTokenUtil()
	finalUserID := userID
	if finalUserID <= 0 {
		finalUserID = -1
	}
	internalToken, err := tokenUtil.GenerateInternalToken(finalUserID, "gozero")
	if err == nil {
		req.Header.Set("X-Internal-Token", "Bearer "+internalToken)
	}

	if contentType != "" && req.Header.Get("Content-Type") == "" {
		req.Header.Set("Content-Type", contentType)
	}

	client := &http.Client{Timeout: defaultRequestTimeout}
	resp, err := client.Do(req)
	if err != nil {
		return Result{}, err
	}
	defer resp.Body.Close()

	body1, err := io.ReadAll(resp.Body)
	if err != nil {
		return Result{}, err
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		errorMsg := fmt.Sprintf(utils.UNEXPECTED_STATUS_CODE, resp.StatusCode, string(body1))
		return Result{}, errors.New(errorMsg)
	}

	if err := json.Unmarshal(body1, &result); err != nil {
		return Result{}, err
	}

	if result.Code != 1 {
		errorMsg := fmt.Sprintf(utils.SERVICE_CALL_FAILED, result.Msg)
		return Result{}, errors.New(errorMsg)
	}

	return result, nil
}

func buildRequestBody(data any) ([]byte, string, error) {
	switch v := data.(type) {
	case nil:
		return nil, "", nil
	case map[string]any:
		jsonData, err := json.Marshal(v)
		if err != nil {
			return nil, "", err
		}
		return jsonData, "application/json", nil
	case string:
		return []byte(v), "application/json", nil
	case []byte:
		return v, "application/json", nil
	case url.Values:
		return []byte(v.Encode()), "application/x-www-form-urlencoded", nil
	default:
		jsonData, err := json.Marshal(v)
		if err != nil {
			return nil, "", err
		}
		return jsonData, "application/json", nil
	}
}

func shouldRetry(err error) bool {
	if err == nil {
		return false
	}

	if errors.Is(err, context.DeadlineExceeded) || errors.Is(err, context.Canceled) {
		return true
	}

	errMsg := err.Error()
	return strings.Contains(errMsg, "异常状态码: 5") ||
		strings.Contains(errMsg, "connection refused") ||
		strings.Contains(errMsg, "timeout") ||
		strings.Contains(errMsg, "EOF")
}

func calculateBackoff(attempt int) time.Duration {
	backoff := float64(initialRetryBackoff) * math.Pow(2, float64(attempt-1))
	if backoff > float64(maxRetryBackoff) {
		backoff = float64(maxRetryBackoff)
	}
	return time.Duration(backoff)
}

// 私有方法：获取服务实例列表
func (sd *ServiceDiscovery) getServiceInstances(serviceName string) ([]model.Instance, error) {
	// 带缓存的查询（每30秒更新）
	if v, ok := sd.serviceMap.Load(serviceName); ok {
		if cached, ok := v.(*serviceCache); ok && time.Since(cached.timestamp) < 30*time.Second {
			return cached.instances, nil
		}
	}

	// 从Nacos查询实例
	instances, err := sd.namingClient.SelectInstances(vo.SelectInstancesParam{
		ServiceName: serviceName,
		GroupName:   "DEFAULT_GROUP",
		HealthyOnly: true,
	})
	if err != nil {
		return nil, errors.New(utils.SERVICE_DISCOVERY_ERROR)
	}
	if len(instances) == 0 {
		return nil, errors.New(utils.NO_AVAILABLE_SERVICE_INSTANCE)
	}

	// 更新缓存
	sd.serviceMap.Store(serviceName, &serviceCache{
		instances: instances,
		timestamp: time.Now(),
	})

	return instances, nil
}

type serviceCache struct {
	instances []model.Instance
	timestamp time.Time
}
