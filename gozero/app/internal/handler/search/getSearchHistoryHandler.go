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

// @Summary 获取用户搜索历史
// @Description 获取指定用户最近10条搜索关键词列表
// @Tags 文章
// @Accept json
// @Produce json
// @Param userId path int true "用户ID"
// @Success 200 {object} map[string]interface{} "包含关键词列表的数据"
// @Failure 400 {object} map[string]interface{} "参数错误"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /search/history/{userId} [get]
// 获取搜索历史
func GetSearchHistoryHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		var req types.GetSearchHistoryReq
		if err := httpx.Parse(r, &req); err != nil {
			utils.Error(w, err.Error())
			return
		}

		l := search.NewGetSearchHistoryLogic(r.Context(), svcCtx)
		resp, err := l.GetSearchHistory(&req)
		if err != nil {
			utils.Error(w, err.Error())
		} else {
			utils.Success(w, resp)
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQChannel, svcCtx.Logger, handler, "获取搜索历史")
}
