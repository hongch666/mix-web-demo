package client

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/ioutil"
	"strings"

	"github.com/hongch666/mix-web-demo/gin/common/keys"
	"github.com/hongch666/mix-web-demo/gin/common/utils"

	"net/http"
	"net/url"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/nacos-group/nacos-sdk-go/v2/clients/naming_client"
	"github.com/nacos-group/nacos-sdk-go/v2/model"
	"github.com/nacos-group/nacos-sdk-go/v2/vo"
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
func (sd *ServiceDiscovery) CallService(c *gin.Context, serviceName string, path string, opts RequestOptions) (Result, error) {
	var result Result
	// 1. 获取服务实例（带负载均衡）
	instance, err := sd.GetInstance(serviceName)
	if err != nil {
		return Result{}, err
	}

	// 2. 构建基础URL
	baseURL := fmt.Sprintf("http://%s:%d%s", instance.Ip, instance.Port, path)

	// 3. 处理路径参数（支持RESTful风格）
	if opts.PathParams != nil {
		for key, value := range opts.PathParams {
			baseURL = strings.Replace(baseURL, ":"+key, value, 1)
		}
	}

	// 4. 添加查询参数
	if opts.QueryParams != nil {
		baseURL += "?" + opts.QueryParams.Encode()
	}

	// 5. 创建请求体Reader（不再合并 userID/username 到 body）
	var body io.Reader
	switch data := opts.BodyData.(type) {
	case nil:
		// 没有传递请求体
		body = nil
	case map[string]any:
		jsonData, err := json.Marshal(data)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": utils.JSON_SERIALIZATION_ERROR})
			return Result{}, err
		}
		body = bytes.NewReader(jsonData)
	case string:
		body = strings.NewReader(data)
	case []byte:
		body = bytes.NewReader(data)
	case url.Values:
		body = strings.NewReader(data.Encode())
	default:
		jsonData, err := json.Marshal(data)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": utils.JSON_SERIALIZATION_ERROR})
			return Result{}, err
		}
		body = bytes.NewReader(jsonData)
	}

	// 6. 创建HTTP请求对象
	req, err := http.NewRequest(opts.Method, baseURL, body)
	if err != nil {
		return Result{}, err
	}

	// 7. 设置请求头（自动加上用户信息）
	if opts.Headers != nil {
		for k, v := range opts.Headers {
			req.Header.Set(k, v)
		}
	}
	// 自动加上用户信息到请求头
	ctx := c.Request.Context()
	userID, _ := ctx.Value(keys.UserIDKey).(int64)
	username, _ := ctx.Value(keys.UsernameKey).(string)
	req.Header.Set("X-User-Id", fmt.Sprintf("%d", userID))
	req.Header.Set("X-Username", username)

	// 自动生成并添加内部服务令牌到请求头 (没有用户ID时用-1代表系统调用)
	tokenUtil := utils.GetTokenUtil()
	finalUserID := userID
	if finalUserID <= 0 {
		finalUserID = -1
	}
	internalToken, err := tokenUtil.GenerateInternalToken(finalUserID, "gin")
	if err == nil {
		req.Header.Set("X-Internal-Token", "Bearer "+internalToken)
	}

	// 自动设置Content-Type
	if body != nil && req.Header.Get("Content-Type") == "" {
		switch opts.BodyData.(type) {
		case url.Values:
			req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		default:
			req.Header.Set("Content-Type", "application/json")
		}
	}

	// 8. 发送HTTP请求（带超时控制）
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return Result{}, err
	}
	defer resp.Body.Close()

	// 9. 读取响应体
	body1, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return Result{}, err
	}

	// 10. 检查HTTP状态码
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		errorMsg := fmt.Sprintf(utils.UNEXPECTED_STATUS_CODE, resp.StatusCode, string(body1))
		return Result{}, errors.New(errorMsg)
	}

	// 11. JSON解析
	if err := json.Unmarshal(body1, &result); err != nil {
		return Result{}, err
	}

	// 12. 检查响应业务状态码（code不为1表示业务错误）
	if result.Code != 1 {
		errorMsg := fmt.Sprintf(utils.SERVICE_CALL_FAILED, result.Msg)
		return Result{}, errors.New(errorMsg)
	}

	// 13. 返回解析结果
	return result, nil
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
