package utils

import (
	"net/http"

	"app/common/constants"

	"github.com/zeromicro/go-zero/rest/httpx"
)

// Success 返回成功响应
func Success(w http.ResponseWriter, data any) {
	httpx.WriteJson(w, http.StatusOK, map[string]any{
		"code": constants.HttpOK,
		"msg":  "success",
		"data": data,
	})
}

// Error 返回错误响应，code 为 3 位 HTTP 状态码
func Error(w http.ResponseWriter, code int, message string) {
	httpx.WriteJson(w, code, map[string]any{
		"code": code,
		"msg":  message,
		"data": nil,
	})
}

// businessError 包含 Code 和 Message 的业务错误接口
type businessError interface {
	BusinessCode() int
	BusinessMessage() string
}

// HandleError 统一处理错误响应，如果是 BusinessError 则使用其状态码，否则返回 500
func HandleError(w http.ResponseWriter, err error) {
	if be, ok := err.(businessError); ok {
		Error(w, be.BusinessCode(), be.BusinessMessage())
	} else {
		Error(w, constants.HttpInternalServerError, err.Error())
	}
}
