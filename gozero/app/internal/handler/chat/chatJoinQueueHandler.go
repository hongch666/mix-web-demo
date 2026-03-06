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

// @Summary 		加入队列
// @Description 	用户加入聊天队列
// @Tags 			chat
// @Accept  		json
// @Produce 		json
// @Param   		request body types.ChatJoinQueueReq true "用户ID"
// @Success 		200 {object} types.ChatJoinQueueResp "加入结果"
// @Failure 		400 {object} map[string]interface{} "请求参数错误"
// @Failure 		500 {object} map[string]interface{} "服务器错误"
// @Router  		/user-chat/join [post]
// 加入队列
func ChatJoinQueueHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		var req types.ChatJoinQueueReq
		if err := httpx.Parse(r, &req); err != nil {
			utils.Error(w, http.StatusBadRequest, err.Error())
			return
		}

		l := chat.NewChatJoinQueueLogic(r.Context(), svcCtx)
		resp, err := l.ChatJoinQueue(&req)
		if err != nil {
			utils.Error(w, http.StatusInternalServerError, err.Error())
		} else {
			utils.Success(w, resp)
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQChannel, svcCtx.Logger, handler, "加入队列")
}
