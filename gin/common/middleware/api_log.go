package middleware

import (
	"bytes"
	"encoding/json"
	"fmt"
	"gin_proj/common/ctxkey"
	"gin_proj/common/utils"
	"gin_proj/config"
	"io"
	"net/url"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
)

// ApiLogMiddleware 创建API日志中间件
// description: 自定义描述信息，例如 "搜索文章"
func ApiLogMiddleware(description string) gin.HandlerFunc {
	return func(c *gin.Context) {
		// 记录开始时间，用于计算处理耗时
		start := time.Now()
		// 获取用户信息
		userID, _ := c.Request.Context().Value(ctxkey.UserIDKey).(int64)
		username, _ := c.Request.Context().Value(ctxkey.UsernameKey).(string)

		// 获取请求信息
		method := c.Request.Method
		path := c.FullPath()
		if path == "" {
			path = c.Request.URL.Path
		}

		// 构建基础日志信息
		logInfo := map[string]interface{}{
			"用户ID": userID,
			"用户名":  username,
			"请求方法": method,
			"请求路径": path,
			"描述":   description,
		}

		// 获取路径参数
		pathParams := extractPathParams(c)
		if len(pathParams) > 0 {
			logInfo["路径参数"] = pathParams
		}

		// 获取查询参数
		queryParams := extractQueryParams(c)
		if len(queryParams) > 0 {
			logInfo["查询参数"] = queryParams
		}

		// 获取请求体（仅对POST、PUT、PATCH请求）
		if method == "POST" || method == "PUT" || method == "PATCH" {
			if bodyData := extractRequestBody(c); bodyData != nil {
				logInfo["请求体"] = bodyData
			}
		}

		// 记录日志（请求开始）
		logMessage := formatLogMessage(method, path, description, userID, username, logInfo)
		utils.LogInfo(logMessage)

		// 继续处理请求
		c.Next()

		// 请求处理完成，记录耗时（毫秒）
		durationMs := time.Since(start).Milliseconds()
		timeMessage := fmt.Sprintf("%s %s 使用了%dms", method, path, durationMs)
		utils.LogInfo(timeMessage)

		// 🚀 发送 API 日志到 RabbitMQ
		sendApiLogToQueue(userID, username, method, path, description, pathParams, queryParams, logInfo["请求体"], durationMs)
	}
}

// extractPathParams 提取路径参数
func extractPathParams(c *gin.Context) map[string]string {
	params := make(map[string]string)

	// 遍历 Gin 的 Params
	for _, param := range c.Params {
		params[param.Key] = param.Value
	}

	return params
}

// extractQueryParams 提取查询参数
func extractQueryParams(c *gin.Context) map[string]interface{} {
	queryParams := make(map[string]interface{})

	// 获取所有查询参数
	values := c.Request.URL.Query()
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
func extractRequestBody(c *gin.Context) interface{} {
	if c.Request.Body == nil {
		return nil
	}

	// 读取请求体
	bodyBytes, err := io.ReadAll(c.Request.Body)
	if err != nil {
		return nil
	}

	// 重新设置请求体，以便后续处理可以再次读取
	c.Request.Body = io.NopCloser(bytes.NewBuffer(bodyBytes))

	if len(bodyBytes) == 0 {
		return nil
	}

	// 尝试解析为JSON
	var jsonData interface{}
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
func parseFormData(data string) (map[string]interface{}, error) {
	values, err := url.ParseQuery(data)
	if err != nil {
		return nil, err
	}

	result := make(map[string]interface{})
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
// 格式: 用户ID:用户名 方法 路径: 描述信息
func formatLogMessage(method, path, description string, userID int64, username string, logInfo map[string]interface{}) string {
	// 基础信息按照指定格式
	var message string
	if userID > 0 {
		message = fmt.Sprintf("用户%d:%s %s %s: %s", userID, username, method, path, description)
	} else {
		message = fmt.Sprintf("匿名用户 %s %s: %s", method, path, description)
	}

	// 添加参数信息
	var details []string

	if pathParams, ok := logInfo["路径参数"].(map[string]string); ok && len(pathParams) > 0 {
		if paramsJSON, err := json.Marshal(pathParams); err == nil {
			details = append(details, "路径参数: "+string(paramsJSON))
		}
	}

	if queryParams, ok := logInfo["查询参数"].(map[string]interface{}); ok && len(queryParams) > 0 {
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

// sendApiLogToQueue 发送 API 日志到 RabbitMQ
func sendApiLogToQueue(userID int64, username, method, path, description string,
	pathParams map[string]string, queryParams map[string]interface{}, requestBody interface{}, responseTimeMs int64) {

	// 构建 API 日志消息（统一格式：snake_case）
	apiLogMessage := map[string]interface{}{
		"user_id":         userID,
		"username":        username,
		"api_description": description,
		"api_path":        path,
		"api_method":      method,
		"query_params":    queryParams,
		"path_params":     pathParams,
		"request_body":    requestBody,
		"response_time":   responseTimeMs,
	}

	// 序列化为 JSON
	messageJSON, err := json.Marshal(apiLogMessage)
	if err != nil {
		utils.LogError(fmt.Sprintf("序列化 API 日志消息失败: %v", err))
		return
	}

	// 发送到 RabbitMQ
	if config.RabbitMQ != nil {
		err = config.RabbitMQ.Send("api-log-queue", string(messageJSON))
		if err != nil {
			utils.LogError(fmt.Sprintf("发送 API 日志到队列失败: %v", err))
		} else {
			utils.LogInfo("API 日志已发送到队列")
		}
	} else {
		utils.LogError("RabbitMQ 未初始化，无法发送 API 日志")
	}
}
