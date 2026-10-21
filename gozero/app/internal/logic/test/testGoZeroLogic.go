// Code scaffolded by goctl. Safe to edit.

package test

import (
	"context"

	"app/common/constants"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

// TestGoZeroLogic 处理测试 GoZero 服务接口请求的逻辑对象
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
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

// TestGoZero 处理测试 GoZero 服务接口请求，直接返回欢迎消息
func (l *TestGoZeroLogic) TestGoZero() (resp *types.TestGoZeroResp, err error) {
	// 直接返回GoZero的欢迎消息
	resp = &types.TestGoZeroResp{
		Data: constants.TEST_MESSAGE,
	}
	return
}
