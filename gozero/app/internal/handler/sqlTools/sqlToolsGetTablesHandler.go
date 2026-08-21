// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package sqlTools

import (
	"net/http"

	"app/common/constants"
	"app/common/utils"
	"app/internal/logic/sqlTools"
	"app/internal/middleware"
	"app/internal/svc"
	"app/internal/types"

	"github.com/zeromicro/go-zero/rest/httpx"
)

// 获取表结构信息
func SqlToolsGetTablesHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		var req types.SqlToolsGetTablesReq
		if err := httpx.Parse(r, &req); err != nil {
			utils.Error(w, constants.HttpBadRequest, err.Error())
			return
		}

		l := sqlTools.NewSqlToolsGetTablesLogic(r.Context(), svcCtx)
		resp, err := l.SqlToolsGetTables(&req)
		if err != nil {
			utils.HandleError(w, err)
			return
		}
		utils.Success(w, resp)
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQPublisher, svcCtx.Logger, handler, constants.API_LOG_SQL_TOOLS_GET_TABLES)
}
