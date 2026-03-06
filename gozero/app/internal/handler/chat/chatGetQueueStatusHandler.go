// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"net/http"

	"app/common/utils"
	"app/internal/logic/chat"
	"app/internal/middleware"
	"app/internal/svc"
)

// @Summary 获取队列状态
// @Description 获取当前在队列中的所有用户
// @Tags 聊天
// @Produce json
// @Success 		200 {object} types.ChatGetQueueStatusResp "队列状态"
// @Router /user-chat/queue [get]
// 获取队列状态
func ChatGetQueueStatusHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		l := chat.NewChatGetQueueStatusLogic(r.Context(), svcCtx)
		resp, err := l.ChatGetQueueStatus()
		if err != nil {
			utils.Error(w, err.Error())
		} else {
			utils.Success(w, resp)
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQChannel, svcCtx.Logger, handler, "获取队列状态")
}
