// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package search

import (
	"net/http"

	"app/common/utils"
	"app/internal/logic/search"
	"app/internal/middleware"
	"app/internal/svc"
	"app/internal/types"

	"github.com/zeromicro/go-zero/rest/httpx"
)

// @Summary 		获取搜索历史
// @Description 	获取用户的历史搜索记录
// @Tags 			search
// @Accept  		json
// @Produce 		json
// @Param   		userId path string true "用户ID"
// @Param   		page query int false "页码" default(1)
// @Param   		size query int false "每页数量" default(10)
// @Success 		200 {object} map[string]interface{} "搜索历史列表"
// @Failure 		400 {object} map[string]interface{} "请求参数错误"
// @Failure 		500 {object} map[string]interface{} "服务器错误"
// @Router  		/search/history/{userId} [get]
// 获取搜索历史
func GetSearchHistoryHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		var req types.GetSearchHistoryReq
		if err := httpx.Parse(r, &req); err != nil {
			utils.Error(w, http.StatusBadRequest, err.Error())
			return
		}

		l := search.NewGetSearchHistoryLogic(r.Context(), svcCtx)
		resp, err := l.GetSearchHistory(&req)
		if err != nil {
			utils.Error(w, http.StatusInternalServerError, err.Error())
		} else {
			utils.Success(w, resp)
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQChannel, svcCtx.Logger, handler, "获取搜索历史")
}
