// Code scaffolded by goctl. Safe to edit.

package {{.PkgName}}

import (
	"net/http"

	"app/common/constants"
	"app/common/utils"
	"app/internal/middleware"
	{{if .HasRequest}}"app/internal/types"{{end}}
	{{.ImportPackages}}

	{{if .HasRequest}}"github.com/zeromicro/go-zero/rest/httpx"{{end}}
)

{{if .HasDoc}}{{.Doc}}{{end}}
func {{.HandlerName}}(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		{{if .HasRequest}}var req types.{{.RequestType}}
		if err := httpx.Parse(r, &req); err != nil {
			utils.HandleErrorWithCode(w, err, constants.HttpBadRequest)
			return
		}

		{{end}}l := {{.LogicName}}.New{{.LogicType}}(r.Context(), svcCtx)
		{{if .HasResp}}resp, {{end}}err := l.{{.Call}}({{if .HasRequest}}&req{{end}})
		if err != nil {
			utils.HandleError(w, err)
			return
		}
		{{if .HasResp}}utils.Success(w, resp){{else}}utils.Success(w, nil){{end}}
	}
	// TODO: 若接口涉及敏感字段，请在下面数组添加字段名（如 "password", "captcha", "token"）
	return middleware.ApplyApiLog(svcCtx.RabbitMQPublisher, svcCtx.Logger, handler, constants.API_LOG_PENDING_DESCRIPTION)
}
