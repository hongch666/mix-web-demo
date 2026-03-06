// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package chat

import (
	"net/http"

	"app/common/utils"
	"app/internal/logic/chat"
	"app/internal/middleware"
	"app/internal/svc"
	"app/internal/types"

	"github.com/zeromicro/go-zero/rest/httpx"
)

// @Summary 发送聊天消息
// @Description 发送聊天消息，先保存到数据库，再通过WebSocket发送给在线用户
// @Tags 聊天
// @Accept json
// @Produce json
// @Param   		request body types.ChatSendMessageReq true "消息内容"
// @Success 		200 {object} map[string]interface{} "消息发送成功"
// @Router /user-chat/send [post]
// 发送消息
func ChatSendMessageHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		var req types.ChatSendMessageReq
		if err := httpx.Parse(r, &req); err != nil {
			utils.Error(w, err.Error())
			return
		}

		l := chat.NewChatSendMessageLogic(r.Context(), svcCtx)
		resp, err := l.ChatSendMessage(&req)
		if err != nil {
			utils.Error(w, err.Error())
		} else {
			utils.Success(w, resp)
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQChannel, svcCtx.Logger, handler, "发送消息")
}
