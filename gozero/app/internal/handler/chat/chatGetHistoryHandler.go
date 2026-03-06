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

// @Summary 		获取聊天历史
// @Description 	获取两个用户之间的聊天消息历史
// @Tags 			chat
// @Accept  		json
// @Produce 		json
// @Param   		request body types.ChatGetHistoryReq true "查询参数"
// @Success 		200 {object} types.ChatGetHistoryResp "聊天历史"
// @Failure 		400 {object} map[string]interface{} "请求参数错误"
// @Failure 		500 {object} map[string]interface{} "服务器错误"
// @Router  		/user-chat/history [post]
// 获取聊天历史
func ChatGetHistoryHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		var req types.ChatGetHistoryReq
		if err := httpx.Parse(r, &req); err != nil {
			utils.Error(w, http.StatusBadRequest, err.Error())
			return
		}

		l := chat.NewChatGetHistoryLogic(r.Context(), svcCtx)
		resp, err := l.ChatGetHistory(&req)
		if err != nil {
			utils.Error(w, http.StatusInternalServerError, err.Error())
		} else {
			utils.Success(w, resp)
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQChannel, svcCtx.Logger, handler, "获取聊天历史")
}
