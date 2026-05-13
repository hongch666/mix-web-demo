package test

import (
	"context"

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
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

func (l *TestFastAPILogic) TestFastAPI() (resp *types.TestFastAPIResp, err error) {
	result, err := l.svcCtx.FastapiClient.Test(l.ctx)
	if err != nil {
		l.Error(utils.PARSE_ERR + ": " + err.Error())
		panic(exceptions.NewBadGatewayError(utils.PARSE_ERR, err.Error()))
	}

	data, ok := result.Data.(string)
	if !ok {
		data = ""
	}
	resp = &types.TestFastAPIResp{
		Data: data,
	}

	return
}
