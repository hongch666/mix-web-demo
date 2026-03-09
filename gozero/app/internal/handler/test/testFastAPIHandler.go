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

// 测试FastAPI服务
func TestFastAPIHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		l := test.NewTestFastAPILogic(r.Context(), svcCtx)
		resp, err := l.TestFastAPI()
		if err != nil {
			utils.Error(w, err.Error())
		} else {
			utils.Success(w, resp.Data)
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQChannel, svcCtx.Logger, handler, "测试FastAPI服务")
}
