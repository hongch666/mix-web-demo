package test

import (
	"app/common/constants"
	"context"

	"app/common/exceptions"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type TestNestJSLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// 测试NestJS服务
func NewTestNestJSLogic(ctx context.Context, svcCtx *svc.ServiceContext) *TestNestJSLogic {
	return &TestNestJSLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

func (l *TestNestJSLogic) TestNestJS() (resp *types.TestNestJSResp, err error) {
	result, err := l.svcCtx.NestjsClient.Test(l.ctx)
	if err != nil {
		l.Error(constants.PARSE_ERR + ": " + err.Error())
		return nil, exceptions.NewBadGatewayError(constants.PARSE_ERR, err.Error())
	}

	data, ok := result.Data.(string)
	if !ok {
		data = ""
	}
	resp = &types.TestNestJSResp{
		Data: data,
	}

	return
}
