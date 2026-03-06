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

// @Summary 		获取队列状态
// @Description 	获取当前聊天队列的在线用户和队列长度
// @Tags 			chat
// @Accept  		json
// @Produce 		json
// @Success 		200 {object} types.ChatGetQueueStatusResp "队列状态"
// @Failure 		500 {object} map[string]interface{} "服务器错误"
// @Router  		/user-chat/queue [get]
// 获取队列状态
func ChatGetQueueStatusHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		l := chat.NewChatGetQueueStatusLogic(r.Context(), svcCtx)
		resp, err := l.ChatGetQueueStatus()
		if err != nil {
			utils.Error(w, http.StatusInternalServerError, err.Error())
		} else {
			utils.Success(w, resp)
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQChannel, svcCtx.Logger, handler, "获取队列状态")
}
