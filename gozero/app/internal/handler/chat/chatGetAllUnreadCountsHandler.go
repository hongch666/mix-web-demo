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

// @Summary 		获取所有未读消息数
// @Description 	获取用户的所有未读消息总数
// @Tags 			chat
// @Accept  		json
// @Produce 		json
// @Param   		request body types.ChatGetAllUnreadCountsReq true "用户ID"
// @Success 		200 {object} types.ChatGetAllUnreadCountsResp "未读消息统计"
// @Failure 		400 {object} map[string]interface{} "请求参数错误"
// @Failure 		500 {object} map[string]interface{} "服务器错误"
// @Router  		/user-chat/all-unread-counts [post]
// 获取所有未读消息数
func ChatGetAllUnreadCountsHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		var req types.ChatGetAllUnreadCountsReq
		if err := httpx.Parse(r, &req); err != nil {
			utils.Error(w, http.StatusBadRequest, err.Error())
			return
		}

		l := chat.NewChatGetAllUnreadCountsLogic(r.Context(), svcCtx)
		resp, err := l.ChatGetAllUnreadCounts(&req)
		if err != nil {
			utils.Error(w, http.StatusInternalServerError, err.Error())
		} else {
			utils.Success(w, resp)
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQChannel, svcCtx.Logger, handler, "获取所有未读消息数")
}
