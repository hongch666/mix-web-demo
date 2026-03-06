package utils

import (
	"net/http"

	"github.com/zeromicro/go-zero/rest/httpx"
)

// Success 返回成功响应
func Success(w http.ResponseWriter, data any) {
	httpx.WriteJson(w, http.StatusOK, map[string]any{
		"code": 1,
		"msg":  "success",
		"data": data,
	})
}

// Error 返回错误响应
func Error(w http.ResponseWriter, message string) {
	httpx.WriteJson(w, http.StatusOK, map[string]any{
		"code": 0,
		"msg":  message,
		"data": nil,
	})
}
