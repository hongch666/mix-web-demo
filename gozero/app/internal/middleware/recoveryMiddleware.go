package middleware

import (
	"net/http"

	"app/common/exceptions"
	"app/common/utils"
)

type RecoveryMiddleware struct {
	*utils.ZeroLogger
}

func NewRecoveryMiddleware(log *utils.ZeroLogger) *RecoveryMiddleware {
	return &RecoveryMiddleware{ZeroLogger: log}
}

// Handle 处理 panic 恢复
func (m *RecoveryMiddleware) Handle(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				// 判断是否是业务异常（可向客户端显示）
				if businessErr, ok := err.(*exceptions.BusinessError); ok {
					// 业务异常：返回对应的错误信息，记录详细堆栈
					m.Error(utils.BUSINESS_ERROR_MESSAGE)
					utils.Error(w, businessErr.Message)
				} else {
					// 其他异常：返回固定的错误信息，记录详细堆栈
					m.Error(utils.STACK_ERROR_MESSAGE)
					utils.Error(w, utils.UNIFIED_ERROR_RESPONSE_MESSAGE)
				}
			}
		}()
		next(w, r)
	}
}
