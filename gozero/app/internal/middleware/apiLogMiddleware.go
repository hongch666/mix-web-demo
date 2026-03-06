package middleware

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"strings"
	"time"

	"app/common/keys"
	"app/common/logger"
	"app/common/utils"

	amqp "github.com/rabbitmq/amqp091-go"
)

type ApiLogMiddleware struct {
	description   string
	rabbitChannel *amqp.Channel
	*logger.ZeroLogger
}

func NewApiLogMiddleware(description string, rabbitChannel *amqp.Channel, log *logger.ZeroLogger) *ApiLogMiddleware {
	return &ApiLogMiddleware{
		description:   description,
		rabbitChannel: rabbitChannel,
		ZeroLogger:    log,
	}
}

// Handle 处理 API 日志
func (m *ApiLogMiddleware) Handle(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// 记录开始时间，用于计算处理耗时
		start := time.Now()

		// 获取用户信息
		userID, _ := r.Context().Value(keys.UserIDKey).(int64)
		username, _ := r.Context().Value(keys.UsernameKey).(string)

		// 如果用户信息为空，则设置为默认值
		if username == "" {
			username = "unknown"
		}

		// 获取请求信息
		method := r.Method
		path := r.URL.Path
		if path == "" {
			path = r.RequestURI
		}

		// 构建基础日志信息
		logInfo := map[string]any{
			"用户ID": userID,
			"用户名":  username,
			"请求方法": method,
			"请求路径": path,
			"描述":   m.description,
		}

		// 获取查询参数
		queryParams := extractQueryParams(r)
		if len(queryParams) > 0 {
			logInfo["查询参数"] = queryParams
		}

		// 获取请求体（仅对POST、PUT、PATCH请求）
		var requestBody any
		if method == "POST" || method == "PUT" || method == "PATCH" {
			requestBody = extractRequestBody(r)
			if requestBody != nil {
				logInfo["请求体"] = requestBody
			}
		}

		// 记录日志（请求开始）
		logMessage := formatLogMessage(method, path, m.description, userID, username, logInfo)
		m.Info(logMessage)

		// 继续处理请求
		next(w, r)

		// 请求处理完成，记录耗时（毫秒）
		durationMs := time.Since(start).Milliseconds()
		timeMessage := fmt.Sprintf(utils.RECORD_DURATION_MESSAGE, method, path, durationMs)
		m.Info(timeMessage)

		// 发送 API 日志到队列（异步，不阻塞主流程）
		if m.ZeroLogger != nil {
			go sendApiLogToQueue(r.Context(), m.ZeroLogger, m.rabbitChannel, userID, username, method, path, m.description, queryParams, requestBody, durationMs)
		}
	}
}

// extractQueryParams 提取查询参数
func extractQueryParams(r *http.Request) map[string]any {
	queryParams := make(map[string]any)

	// 获取所有查询参数
	values := r.URL.Query()
	for key, vals := range values {
		if len(vals) == 1 {
			// 单个值直接存储
			queryParams[key] = vals[0]
		} else if len(vals) > 1 {
			// 多个值存储为数组
			queryParams[key] = vals
		}
	}

	return queryParams
}

// extractRequestBody 提取请求体
func extractRequestBody(r *http.Request) any {
	if r.Body == nil {
		return nil
	}

	// 读取请求体
	bodyBytes, err := io.ReadAll(r.Body)
	if err != nil {
		return nil
	}

	// 重新设置请求体，以便后续处理可以再次读取
	r.Body = io.NopCloser(bytes.NewBuffer(bodyBytes))

	if len(bodyBytes) == 0 {
		return nil
	}

	// 尝试解析为JSON
	var jsonData any
	if err := json.Unmarshal(bodyBytes, &jsonData); err == nil {
		return jsonData
	}

	// 如果不是JSON，尝试解析为表单数据
	if formData, err := parseFormData(string(bodyBytes)); err == nil && len(formData) > 0 {
		return formData
	}

	// 如果都不是，返回原始字符串（截断过长的内容）
	bodyStr := string(bodyBytes)
	if len(bodyStr) > 1000 {
		bodyStr = bodyStr[:1000] + "...[截断]"
	}
	return bodyStr
}

// parseFormData 解析表单数据
func parseFormData(data string) (map[string]any, error) {
	values, err := url.ParseQuery(data)
	if err != nil {
		return nil, err
	}

	result := make(map[string]any)
	for key, vals := range values {
		if len(vals) == 1 {
			result[key] = vals[0]
		} else if len(vals) > 1 {
			result[key] = vals
		}
	}

	return result, nil
}

// formatLogMessage 格式化日志消息
func formatLogMessage(method, path, description string, userID int64, username string, logInfo map[string]any) string {
	// 基础信息按照指定格式
	var message string
	if userID > 0 {
		message = fmt.Sprintf(utils.USER_LOG_MESSAGE, userID, username, method, path, description)
	} else {
		message = fmt.Sprintf(utils.ANONYMOUS_USER_LOG_MESSAGE, method, path, description)
	}

	// 添加参数信息
	var details []string

	if queryParams, ok := logInfo["查询参数"].(map[string]any); ok && len(queryParams) > 0 {
		if paramsJSON, err := json.Marshal(queryParams); err == nil {
			details = append(details, "查询参数: "+string(paramsJSON))
		}
	}

	if requestBody := logInfo["请求体"]; requestBody != nil {
		if bodyJSON, err := json.Marshal(requestBody); err == nil {
			details = append(details, "请求体: "+string(bodyJSON))
		}
	}

	// 拼接详细信息
	if len(details) > 0 {
		message += "\n" + strings.Join(details, "\n")
	}

	return message
}

// sendApiLogToQueue 发送 API 日志到队列（异步处理）
func sendApiLogToQueue(ctx context.Context, lgr *logger.ZeroLogger, rabbitChannel *amqp.Channel, userID int64, username, method, path, description string,
	queryParams map[string]any, requestBody any, responseTimeMs int64) {

	// 构建 API 日志消息（统一格式：snake_case）
	apiLogMessage := map[string]any{
		"user_id":         userID,
		"username":        username,
		"api_description": description,
		"api_path":        path,
		"api_method":      method,
		"query_params":    queryParams,
		"request_body":    requestBody,
		"response_time":   responseTimeMs,
	}

	// 序列化为 JSON
	messageJSON, err := json.Marshal(apiLogMessage)
	if err != nil {
		if lgr != nil {
			lgr.Error(utils.SERIALIZE_API_LOG_FAIL_MESSAGE)
		}
		return
	}

	// 发送到 RabbitMQ
	if rabbitChannel == nil {
		if lgr != nil {
			lgr.Error(utils.RABBITMQ_CHANNEL_NOT_INITIALIZED_MESSAGE)
		}
		return
	}

	// 发布消息到队列
	err = rabbitChannel.PublishWithContext(
		ctx,
		"",              // 默认 exchange
		"api-log-queue", // routing key（队列名）
		false,           // mandatory
		false,           // immediate
		amqp.Publishing{
			ContentType: "application/json",
			Body:        messageJSON,
			Timestamp:   time.Now(),
		},
	)

	if err != nil {
		log.Printf(utils.API_LOG_SEND_FAIL_MESSAGE, err)
		if lgr != nil {
			lgr.Error(utils.SEND_API_LOG_FAIL_MESSAGE)
		}
	} else {
		log.Printf(utils.API_LOG_SEND_SUCCESS_MESSAGE, string(messageJSON))
		if lgr != nil {
			lgr.Info(utils.SEND_API_LOG_SUCCESS_MESSAGE)
		}
	}
}

// WithApiLog 为 handler 添加 API 日志中间件
// WithApiLog 中间件工厂函数
func WithApiLog(rabbitChannel *amqp.Channel, log *logger.ZeroLogger, description string) func(http.HandlerFunc) http.HandlerFunc {
	return func(handler http.HandlerFunc) http.HandlerFunc {
		return NewApiLogMiddleware(description, rabbitChannel, log).Handle(handler)
	}
}

// ApplyApiLog 直接应用 API 日志中间件到 handler
// 用法: return middleware.ApplyApiLog(rabbitChannel, logger, handler, "操作描述")
func ApplyApiLog(rabbitChannel *amqp.Channel, log *logger.ZeroLogger, handler http.HandlerFunc, description string) http.HandlerFunc {
	return WithApiLog(rabbitChannel, log, description)(handler)
}
