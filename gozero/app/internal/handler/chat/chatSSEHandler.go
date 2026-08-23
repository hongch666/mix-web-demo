// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"net/http"
	"strconv"

	"app/common/constants"
	"app/common/utils"
	"app/internal/middleware"
	"app/internal/svc"
)

// SSE连接
func ChatSSEHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	return middleware.ApplyApiLog(svcCtx.RabbitMQPublisher, svcCtx.Logger, func(w http.ResponseWriter, r *http.Request) {
		userIDStr := r.URL.Query().Get("user_id")
		if userIDStr == "" {
			// 尝试从Header获取（网关传递的用户信息）
			userIDStr = r.Header.Get("X-User-Id")
		}

		userID, err := strconv.ParseInt(userIDStr, 10, 64)
		if err != nil || userID <= 0 {
			svcCtx.Logger.Error(constants.USER_ID_LESS)
			utils.Error(w, constants.HttpBadRequest, constants.USER_ID_LESS)
			return
		}

		// 委托给 SSEHub 处理连接的完整生命周期
		svcCtx.SSEHub.HandleConnection(w, r, userID)
	}, constants.API_LOG_SSE_CONNECTION)
}
