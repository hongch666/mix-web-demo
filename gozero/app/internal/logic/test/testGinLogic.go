// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package test

import (
	"context"

	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type TestGinLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
}

// 测试Gin服务
func NewTestGinLogic(ctx context.Context, svcCtx *svc.ServiceContext) *TestGinLogic {
	return &TestGinLogic{
		ctx:    ctx,
		svcCtx: svcCtx,
	}
}

func (l *TestGinLogic) TestGin() (resp *types.TestGinResp, err error) {
	// 直接返回Gin的欢迎消息
	resp = &types.TestGinResp{
		Data: utils.TEST_MESSAGE,
	}
	return
}
