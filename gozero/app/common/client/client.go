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

	"app/common/constants"
	"app/common/keys"
	"app/common/utils"

	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
	"github.com/nacos-group/nacos-sdk-go/v2/model"
	"github.com/nacos-group/nacos-sdk-go/v2/vo"
	"github.com/zeromicro/go-zero/core/breaker"
	"github.com/zeromicro/go-zero/core/logx"
	"github.com/zeromicro/go-zero/rest/httpc"
)

// RemoteCallConfig 远程调用配置
type RemoteCallConfig struct {
	Timeout        time.Duration
	MaxRetries     int
	InitialBackoff time.Duration
	MaxBackoff     time.Duration
}

type ServiceDiscovery struct {
	namingClient naming_client.INamingClient
	httpClient   *http.Client
	services     map[string]httpc.Service // httpc 服务实例，熔断器与链路追踪均绑定服务名，故按服务缓存
	servicesMu   sync.Mutex               // 保护 services 的并发创建
	serviceMap   sync.Map                 // 服务实例缓存
	mu           sync.Mutex               // 保证线程安全
	lbIndex      map[string]uint64        // 负载均衡轮询索引
	config       RemoteCallConfig         // 远程调用配置
	logger       *utils.ZeroLogger        // 运行期日志（可为 nil，nil 时退化为仅 logx）
}

func NewServiceDiscovery(client naming_client.INamingClient, cfg RemoteCallConfig, logger *utils.ZeroLogger) *ServiceDiscovery {
	return &ServiceDiscovery{
		namingClient: client,
		httpClient:   newHTTPClient(cfg),
		services:     make(map[string]httpc.Service),
		lbIndex:      make(map[string]uint64),
		config:       cfg,
		logger:       logger,
	}
}

// newHTTPClient 构建远程调用共用的 HTTP 客户端，统一超时与连接池
func newHTTPClient(cfg RemoteCallConfig) *http.Client {
	return &http.Client{
		Timeout: cfg.Timeout,
		Transport: &http.Transport{
			MaxIdleConns:          100,
			MaxIdleConnsPerHost:   20,
			IdleConnTimeout:       90 * time.Second,
			TLSHandshakeTimeout:   5 * time.Second,
			ResponseHeaderTimeout: cfg.Timeout,
		},
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

// service 按目标服务获取 httpc 服务实例，熔断器与链路追踪均绑定服务名，故按服务缓存复用
func (sd *ServiceDiscovery) service(serviceName string) httpc.Service {
	sd.servicesMu.Lock()
	defer sd.servicesMu.Unlock()

	if svc, ok := sd.services[serviceName]; ok {
		return svc
	}

	// 必须注入自定义客户端，httpc 默认使用的 http.DefaultClient 没有超时
	svc := httpc.NewServiceWithClient(
		constants.RemoteBreakerNamePrefix+serviceName,
		sd.httpClient,
		injectContextHeaders,
	)
	sd.services[serviceName] = svc

	return svc
}

// injectContextHeaders 注入用户上下文与内部令牌，httpc 构建请求时已把调用上下文写入 request
func injectContextHeaders(r *http.Request) *http.Request {
	ctx := r.Context()

	userID, _ := ctx.Value(keys.UserIDKey).(int64)
	username, _ := ctx.Value(keys.UsernameKey).(string)
	sessionID, _ := ctx.Value(keys.SessionIDKey).(string)
	token, _ := ctx.Value(keys.TokenKey).(string)

	r.Header.Set(constants.HeaderUserID, fmt.Sprintf("%d", userID))
	r.Header.Set(constants.HeaderUsername, username)
	r.Header.Set(constants.HeaderSessionID, sessionID)
	if token != "" {
		r.Header.Set(constants.HeaderAuthorization, constants.BearerPrefix+token)
	}

	tokenUtil, err := utils.GetTokenUtil()
	if err != nil {
		return r
	}

	// 无登录用户时以 -1 表示系统调用
	finalUserID := userID
	if finalUserID <= 0 {
		finalUserID = -1
	}
	internalToken, err := tokenUtil.GenerateInternalToken(finalUserID, constants.InternalTokenServiceName)
	if err != nil {
		return r
	}
	r.Header.Set(constants.HeaderInternalToken, constants.BearerPrefix+internalToken)

	return r
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

// CallService 调用下游服务，熔断、链路追踪与耗时日志由 httpc 承担，服务发现与重试仍由本方法控制
func (sd *ServiceDiscovery) CallService(ctx context.Context, serviceName string, path string, opts RequestOptions) (Result, error) {
	result, err := sd.callWithRetry(ctx, serviceName, path, opts)
	if err != nil {
		// httpc 在熔断打开时抢先返回该错误，统一转换为降级提示
		if errors.Is(err, breaker.ErrServiceUnavailable) {
			return Result{}, fmt.Errorf(constants.DOWNSTREAM_SERVICE_UNAVAILABLE_MESSAGE, serviceName, err)
		}
		return Result{}, err
	}

	return result, nil
}

func (sd *ServiceDiscovery) callWithRetry(ctx context.Context, serviceName string, path string, opts RequestOptions) (Result, error) {
	var lastErr error

	for attempt := 1; attempt <= sd.config.MaxRetries; attempt++ {
		result, err := sd.doCall(ctx, serviceName, path, opts)
		if err == nil {
			return result, nil
		}

		lastErr = err
		if !shouldRetry(err) || attempt == sd.config.MaxRetries {
			break
		}

		backoff := calculateBackoff(attempt, sd.config.InitialBackoff, sd.config.MaxBackoff)
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

	attemptCtx, cancel := context.WithTimeout(ctx, sd.config.Timeout)
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
	if contentType != "" && req.Header.Get(constants.HeaderContentType) == "" {
		req.Header.Set(constants.HeaderContentType, contentType)
	}

	// 用户上下文与内部令牌由 httpc 的请求选项注入，发送过程由 httpc 统一处理熔断与链路追踪
	resp, err := sd.service(serviceName).DoRequest(req)
	if err != nil {
		return Result{}, err
	}
	defer resp.Body.Close()

	body1, err := io.ReadAll(resp.Body)
	if err != nil {
		return Result{}, err
	}

	if resp.StatusCode < constants.HttpOK || resp.StatusCode >= constants.HttpMultipleChoices {
		return Result{}, newHTTPStatusError(resp.StatusCode, string(body1))
	}

	if err := json.Unmarshal(body1, &result); err != nil {
		return Result{}, err
	}

	if result.Code < constants.HttpOK || result.Code >= constants.HttpMultipleChoices {
		if sd.logger != nil {
			sd.logger.Errorf(constants.SERVICE_BUSINESS_ERROR_LOG, serviceName, result.Code, result.Msg)
		} else {
			logx.Errorf(constants.SERVICE_BUSINESS_ERROR_LOG, serviceName, result.Code, result.Msg)
		}
		errorMsg := fmt.Sprintf(constants.SERVICE_CALL_FAILED, result.Msg)
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

func calculateBackoff(attempt int, initialBackoff, maxBackoff time.Duration) time.Duration {
	backoff := float64(initialBackoff) * math.Pow(2, float64(attempt-1))
	if backoff > float64(maxBackoff) {
		backoff = float64(maxBackoff)
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
		return nil, errors.New(constants.SERVICE_DISCOVERY_ERROR)
	}
	if len(instances) == 0 {
		return nil, errors.New(constants.NO_AVAILABLE_SERVICE_INSTANCE)
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
