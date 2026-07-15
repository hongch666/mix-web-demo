// Code scaffolded by goctl. Safe to edit.
// goctl {{.version}}

package {{.PkgName}}

import (
	"net/http"

	"app/common/constants"
	"app/common/utils"
	"app/internal/middleware"
	"app/internal/svc"
	{{if .HasRequest}}"app/internal/types"{{end}}
	{{.ImportPackages}}

	{{if .HasRequest}}"github.com/zeromicro/go-zero/rest/httpx"{{end}}
)

{{if .HasDoc}}{{.Doc}}{{end}}
func {{.HandlerName}}(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		{{if .HasRequest}}var req types.{{.RequestType}}
		if err := httpx.Parse(r, &req); err != nil {
			utils.Error(w, constants.HttpBadRequest, err.Error())
			return
		}

		if err := req.Validate(); err != nil {
			utils.HandleError(w, err)
			return
		}

		{{end}}l := {{.LogicName}}.New{{.LogicType}}(r.Context(), svcCtx)
		{{if .HasResp}}resp, {{end}}err := l.{{.Call}}({{if .HasRequest}}&req{{end}})
		if err != nil {
			utils.HandleError(w, err)
		} else {
			{{if .HasResp}}utils.Success(w, resp){{else}}utils.Success(w, nil){{end}}
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQPublisher, svcCtx.Logger, handler, "TODO: 添加接口描述")
}
