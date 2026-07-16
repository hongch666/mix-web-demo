package test

import (
	"net/http"

	"app/common/constants"
	"app/common/utils"
	"app/internal/logic/test"
	"app/internal/middleware"
	"app/internal/svc"
	"app/internal/types"

	"github.com/zeromicro/go-zero/rest/httpx"
)

func SyncEmbeddingHandler(svcCtx *svc.ServiceContext) http.HandlerFunc {
	handler := func(w http.ResponseWriter, r *http.Request) {
		var req types.SyncEmbeddingReq
		if err := httpx.Parse(r, &req); err != nil {
			utils.Error(w, constants.HttpBadRequest, err.Error())
			return
		}

		l := test.NewSyncEmbeddingLogic(r.Context(), svcCtx)
		resp, err := l.SyncEmbedding(&req)
		if err != nil {
			utils.HandleError(w, err)
		} else {
			utils.Success(w, resp)
		}
	}
	return middleware.ApplyApiLog(svcCtx.RabbitMQPublisher, svcCtx.Logger, handler, "手动触发文章向量同步")
}
