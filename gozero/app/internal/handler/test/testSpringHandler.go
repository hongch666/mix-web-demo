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

// @Summary 		测试Spring服务
// @Description 	调用Spring服务进行测试
// @Tags 			test
// @Accept  		json
// @Produce 		json
// @Success 		200 {object} map[string]interface{} "测试成功"
// @Failure 		500 {object} map[string]interface{} "服务器错误"
// @Router  		/api_gin/spring [get]
// 测试Spring服务
func TestSpringHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		l := test.NewTestSpringLogic(r.Context(), svcCtx)
		resp, err := l.TestSpring()
		if err != nil {
			utils.Error(w, http.StatusInternalServerError, err.Error())
		} else {
			utils.Success(w, resp.Data)
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQChannel, svcCtx.Logger, handler, "测试Spring服务")
}
