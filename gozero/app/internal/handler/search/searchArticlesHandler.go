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

// @Summary 搜索文章
// @Description 根据关键词、用户ID、用户名、发布时间范围等条件搜索文章（支持分页）
// @Tags 文章
// @Accept json
// @Produce json
// @Param keyword query string false "搜索关键词（标题/内容/标签）"
// @Param userId query int false "用户ID"
// @Param username query string false "用户名（模糊搜索）"
// @Param startDate query string false "发布时间开始（RFC3339格式）"
// @Param endDate query string false "发布时间结束（RFC3339格式）"
// @Param page query int false "页码（默认1）"
// @Param size query int false "每页数量（默认10）"
// @Success 200 {object} map[string]interface{} "包含 total 和 list 的文章列表"
// @Failure 500 {object} map[string]interface{} "服务器内部错误"
// @Router /search [get]
// 搜索文章
func SearchArticlesHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		var req types.SearchArticlesReq
		if err := httpx.Parse(r, &req); err != nil {
			utils.Error(w, err.Error())
			return
		}

		l := search.NewSearchArticlesLogic(r.Context(), svcCtx)
		resp, err := l.SearchArticles(&req)
		if err != nil {
			utils.Error(w, err.Error())
		} else {
			utils.Success(w, resp)
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQChannel, svcCtx.Logger, handler, "搜索文章")
}
