// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package test

import (
	"context"

	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type TestGoZeroLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// 测试GoZero服务
func NewTestGoZeroLogic(ctx context.Context, svcCtx *svc.ServiceContext) *TestGoZeroLogic {
	return &TestGoZeroLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger,
	}
}

func (l *TestGoZeroLogic) TestGoZero() (resp *types.TestGoZeroResp, err error) {
	// 直接返回GoZero的欢迎消息
	resp = &types.TestGoZeroResp{
		Data: utils.TEST_MESSAGE,
	}
	return
}
