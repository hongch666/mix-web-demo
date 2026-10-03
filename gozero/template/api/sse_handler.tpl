// Code scaffolded by goctl. Safe to edit.
// goctl {{.version}}

{{/*
本模板只在 .api 路由被标记为 SSE 时才会被 goctl 加载，当前项目的 SSE 与 WebSocket 路由都是普通 get 路由，实际走 handler.tpl
警告：本模板是「每请求建 chan + handler 内 select flush」的单机模式，多副本部署会丢消息
本项目实时链路必须改为委托 svcCtx.SSEHub.HandleConnection(w, r, userID)，由 internal/hub 与 common/pubsub 的 Redis Pub/Sub 跨 Pod 分发
*/}}

package {{.PkgName}}

import (
	"encoding/json"
	"fmt"
	"net/http"

	"app/common/constants"
	"app/common/utils"
	"app/internal/middleware"
	"app/internal/svc"
	{{if .HasRequest}}"app/internal/types"{{end}}
	{{.ImportPackages}}

	{{if .HasRequest}}"github.com/zeromicro/go-zero/rest/httpx"{{end}}
	"github.com/zeromicro/go-zero/core/logc"
	"github.com/zeromicro/go-zero/core/threading"
)

{{if .HasDoc}}{{.Doc}}{{end}}
func {{.HandlerName}}(svcCtx *svc.ServiceContext) http.HandlerFunc {
	return middleware.ApplyApiLog(svcCtx.RabbitMQPublisher, svcCtx.Logger, func(w http.ResponseWriter, r *http.Request) {
		{{if .HasRequest}}var req types.{{.RequestType}}
		if err := httpx.Parse(r, &req); err != nil {
			utils.HandleErrorWithCode(w, err, constants.HttpBadRequest)
			return
		}

		{{end}}// Buffer size of 16 is chosen as a reasonable default to balance throughput and memory usage.
		// You can change this based on your application's needs.
		// if your go-zero version less than 1.8.1, you need to add 3 lines below.
		// w.Header().Set("Content-Type", "text/event-stream")
		// w.Header().Set("Cache-Control", "no-cache")
		// w.Header().Set("Connection", "keep-alive")
		client := make(chan {{.ResponseType}}, 16)

		l := {{.LogicName}}.New{{.LogicType}}(r.Context(), svcCtx)
		threading.GoSafeCtx(r.Context(), func() {
			defer close(client)
			err := l.{{.Call}}({{if .HasRequest}}&req, {{end}}client)
			if err != nil {
				logc.Errorw(r.Context(), "{{.HandlerName}}", logc.Field("error", err))
				return
			}
		})

		for {
			select {
			case data, ok := <-client:
				if !ok {
					return
				}
				output, err := json.Marshal(data)
				if err != nil {
					logc.Errorw(r.Context(), "{{.HandlerName}}", logc.Field("error", err))
					continue
				}

				if _, err := fmt.Fprintf(w, "data: %s\n\n", string(output)); err != nil {
					logc.Errorw(r.Context(), "{{.HandlerName}}", logc.Field("error", err))
					return
				}
				if flusher, ok := w.(http.Flusher); ok {
					flusher.Flush()
				}
			case <-r.Context().Done():
				return
			}
		}
	}, constants.API_LOG_PENDING_DESCRIPTION)
}
