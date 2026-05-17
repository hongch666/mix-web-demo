package agent

import (
	"net/http"

	"app/common/utils"
	"app/internal/logic/agent"
	"app/internal/svc"
	"app/internal/types"

	"github.com/zeromicro/go-zero/rest/httpx"
)

func AgentQueryHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req types.AgentQueryReq
		if err := httpx.Parse(r, &req); err != nil {
			utils.Error(w, utils.HttpBadRequest, err.Error())
			return
		}

		l := agent.NewAgentQueryLogic(r.Context(), svcCtx)
		resp, err := l.AgentQuery(&req)
		if err != nil {
			utils.HandleError(w, err)
		} else {
			utils.Success(w, resp)
		}
	}
}
