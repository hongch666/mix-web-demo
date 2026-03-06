// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package test

import (
	"context"

	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"

	"github.com/zeromicro/go-zero/core/logx"
)

type TestGoZeroLogic struct {
	logx.Logger
	ctx    context.Context
	svcCtx *svc.ServiceContext
}

// 测试GoZero服务
func NewTestGoZeroLogic(ctx context.Context, svcCtx *svc.ServiceContext) *TestGoZeroLogic {
	return &TestGoZeroLogic{
		Logger: logx.WithContext(ctx),
		ctx:    ctx,
		svcCtx: svcCtx,
	}
}

func (l *TestGoZeroLogic) TestGoZero() (resp *types.TestGoZeroResp, err error) {
	// 直接返回GoZero的欢迎消息
	resp = &types.TestGoZeroResp{
		Data: utils.TEST_MESSAGE,
	}
	return
}
