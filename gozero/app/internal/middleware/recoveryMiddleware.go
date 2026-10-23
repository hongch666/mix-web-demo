package middleware

import (
	"context"
	"fmt"
	"net/http"
	"runtime/debug"

	"app/common/constants"
	"app/common/exceptions"
	"app/common/utils"
)

// 捕获 handler panic 并统一转换为错误响应的恢复中间件
type RecoveryMiddleware struct {
	*utils.ZeroLogger
}

// NewRecoveryMiddleware 创建 panic 恢复中间件
func NewRecoveryMiddleware(log *utils.ZeroLogger) *RecoveryMiddleware {
	return &RecoveryMiddleware{ZeroLogger: log}
}

// Handle 处理 panic 恢复
func (m *RecoveryMiddleware) Handle(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()
		defer func() {
			if err := recover(); err != nil {
				// 从请求上下文派生 logger，让 panic 堆栈带上本次请求的 trace_id
				m.HandlePanic(ctx, w, err)
			}
		}()
		next(w, r)
	}
}

// HandlePanic 将 panic 转换为错误响应，日志使用调用方传入的上下文派生 logger
func (m *RecoveryMiddleware) HandlePanic(ctx context.Context, w http.ResponseWriter, err any) {
	logger := m.ZeroLogger.WithContext(ctx)
	// 判断是否是业务异常（可向客户端显示）
	if businessErr, ok := err.(*exceptions.BusinessError); ok {
		// 业务异常：返回对应的状态码和错误信息，记录详细堆栈
		logger.Error(fmt.Sprintf(constants.BUSINESS_ERROR_MESSAGE, businessErr.Message, businessErr.Err, debug.Stack()))
		utils.Error(w, businessErr.Code, businessErr.Message)
	} else {
		// 其他异常：返回固定的500错误信息，记录详细堆栈
		logger.Error(fmt.Sprintf(constants.STACK_ERROR_MESSAGE, err, debug.Stack()))
		utils.Error(w, constants.HttpInternalServerError, constants.UNIFIED_ERROR_RESPONSE_MESSAGE)
	}
}
