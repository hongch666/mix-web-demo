// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"net/http"

	"app/common/utils"
	"app/internal/middleware"
	"app/internal/svc"
)

// SSE连接
func ChatSSEHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	return middleware.ApplyApiLog(svcCtx.RabbitMQPublisher, svcCtx.Logger, func(w http.ResponseWriter, r *http.Request) {
		userID := r.URL.Query().Get("user_id")
		if userID == "" {
			// 尝试从Header获取（网关传递的用户信息）
			userID = r.Header.Get("X-User-Id")
		}

		if userID == "" {
			svcCtx.Logger.Error(utils.USER_ID_LESS)
			utils.Error(w, utils.HttpBadRequest, utils.USER_ID_LESS)
			return
		}

		// 委托给 SSEHub 处理连接的完整生命周期
		svcCtx.SSEHub.HandleConnection(w, r, userID)
	}, "SSE连接")
}
