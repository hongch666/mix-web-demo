// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package task

import (
	"net/http"

	"app/common/constants"
	"app/common/utils"
	"app/internal/logic/task"
	"app/internal/middleware"
	"app/internal/svc"
	"app/internal/types"

	"github.com/zeromicro/go-zero/rest/httpx"
)

// 手动触发同步ES任务
func SyncESHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		var req types.SyncESReq
		if err := httpx.Parse(r, &req); err != nil {
			utils.Error(w, constants.HttpBadRequest, err.Error())
			return
		}

		l := task.NewSyncESLogic(r.Context(), svcCtx)
		resp, err := l.SyncES(&req)
		if err != nil {
			utils.HandleError(w, err)
		} else {
			utils.Success(w, resp)
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQPublisher, svcCtx.Logger, handler, "手动触发同步ES任务")
}
