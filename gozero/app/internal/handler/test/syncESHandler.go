// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package test

import (
	"net/http"

	"app/common/utils"
	"app/internal/logic/test"
	"app/internal/middleware"
	"app/internal/svc"
	"app/internal/types"

	"github.com/zeromicro/go-zero/rest/httpx"
)

// @Summary 调用同步ES的测试
// @Description 查看是否同步成功
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gozero/syncer [post]
// 手动触发同步ES任务
func SyncESHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		var req types.SyncESReq
		if err := httpx.Parse(r, &req); err != nil {
			utils.Error(w, err.Error())
			return
		}

		l := test.NewSyncESLogic(r.Context(), svcCtx)
		resp, err := l.SyncES(&req)
		if err != nil {
			utils.Error(w, err.Error())
		} else {
			utils.Success(w, resp)
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQChannel, svcCtx.Logger, handler, "手动触发同步ES任务")
}
