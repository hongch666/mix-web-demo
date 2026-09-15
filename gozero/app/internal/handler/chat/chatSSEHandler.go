// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"net/http"

	"app/common/constants"
	"app/common/utils"
	"app/internal/logic/chat"
	"app/internal/middleware"
	"app/internal/svc"
	"app/internal/types"

	"github.com/zeromicro/go-zero/rest/httpx"
)

// SSE连接
func ChatSSEHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	return middleware.ApplyApiLog(svcCtx.RabbitMQPublisher, svcCtx.Logger, func(w http.ResponseWriter, r *http.Request) {
		var req types.ChatSSEConnectReq
		if err := httpx.Parse(r, &req); err != nil {
			utils.Error(w, constants.HttpBadRequest, err.Error())
			return
		}

		if err := req.Validate(); err != nil {
			utils.HandleError(w, err)
			return
		}

		l := chat.NewChatSSELogic(r.Context(), svcCtx)
		userID, err := l.ResolveUserID(&req, r.Header.Get("X-User-Id"))
		if err != nil {
			utils.HandleError(w, err)
			return
		}

		svcCtx.Logger.Info(constants.SSE_CONNECTION_ESTABLISHED_MESSAGE)

		// 委托给 SSEHub 处理连接的完整生命周期
		svcCtx.SSEHub.HandleConnection(w, r, userID)
	}, constants.API_LOG_SSE_CONNECTION)
}
