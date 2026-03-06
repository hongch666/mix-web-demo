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

// @Summary 调用Spring的测试
// @Description 输出欢迎信息
// @Tags 测试
// @Success 200 {object} map[string]interface{}
// @Router /api_gozero/spring [get]
func TestSpringHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		l := test.NewTestSpringLogic(r.Context(), svcCtx)
		resp, err := l.TestSpring()
		if err != nil {
			utils.Error(w, err.Error())
		} else {
			utils.Success(w, resp.Data)
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQChannel, svcCtx.Logger, handler, "测试Spring服务")
}
