// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package test

import (
	"net/http"

	"app/common/utils"
	"app/internal/logic/test"
	"app/internal/middleware"
	"app/internal/svc"
)

// @Summary GoZero自己的测试
// @Description 输出欢迎信息
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gozero/gozero [get]
// 测试GoZero服务
func TestGoZeroHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		l := test.NewTestGoZeroLogic(r.Context(), svcCtx)
		resp, err := l.TestGoZero()
		if err != nil {
			utils.Error(w, err.Error())
		} else {
			utils.Success(w, resp.Data)
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQChannel, svcCtx.Logger, handler, "测试GoZero服务")
}
