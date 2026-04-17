// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package test

import (
	"context"
	"fmt"
	"net/http"

	"app/common/client"
	"app/common/exceptions"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type TestFastAPILogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// 测试FastAPI服务
func NewTestFastAPILogic(ctx context.Context, svcCtx *svc.ServiceContext) *TestFastAPILogic {
	return &TestFastAPILogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger,
	}
}

func (l *TestFastAPILogic) TestFastAPI() (resp *types.TestFastAPIResp, err error) {
	// 通过Nacos服务发现调用FastAPI服务
	opts := client.RequestOptions{
		Method: http.MethodGet,
	}
	sd := client.NewServiceDiscovery(l.svcCtx.NamingClient)
	result, err := sd.CallService(l.ctx, "fastapi", "/api_fastapi/fastapi", opts)
	if err != nil {
		l.Error(fmt.Sprintf(utils.PARSE_ERR+": %v", err))
		panic(exceptions.NewBusinessError(utils.PARSE_ERR, err.Error()))
	}

	resultData := result.Data.(string)
	resp = &types.TestFastAPIResp{
		Data: resultData,
	}

	return
}
