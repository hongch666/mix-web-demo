package test

import (
	"context"

	"app/common/exceptions"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type TestSpringLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// 测试Spring服务
func NewTestSpringLogic(ctx context.Context, svcCtx *svc.ServiceContext) *TestSpringLogic {
	return &TestSpringLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

func (l *TestSpringLogic) TestSpring() (resp *types.TestSpringResp, err error) {
	result, err := l.svcCtx.SpringClient.Test(l.ctx)
	if err != nil {
		l.Error(utils.PARSE_ERR + ": " + err.Error())
		panic(exceptions.NewBadGatewayError(utils.PARSE_ERR, err.Error()))
	}

	data, ok := result.Data.(string)
	if !ok {
		data = ""
	}
	resp = &types.TestSpringResp{
		Data: data,
	}

	return
}
