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

// @Summary 获取两个用户间的未读消息数
// @Description 获取指定用户与另一个用户间的未读消息数
// @Tags 聊天
// @Accept json
// @Produce json
// @Param   		request body types.ChatGetUnreadCountReq true "查询参数"
// @Success 		200 {object} types.ChatGetUnreadCountResp "未读消息数"
// @Router /user-chat/unread-count [post]
// 获取未读消息数
func ChatGetUnreadCountHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		var req types.ChatGetUnreadCountReq
		if err := httpx.Parse(r, &req); err != nil {
			utils.Error(w, err.Error())
			return
		}

		l := chat.NewChatGetUnreadCountLogic(r.Context(), svcCtx)
		resp, err := l.ChatGetUnreadCount(&req)
		if err != nil {
			utils.Error(w, err.Error())
		} else {
			utils.Success(w, resp)
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQChannel, svcCtx.Logger, handler, "获取未读消息数")
}
