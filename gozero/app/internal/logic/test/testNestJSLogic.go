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
		ZeroLogger: svcCtx.Logger,
	}
}

func (l *TestNestJSLogic) TestNestJS() (resp *types.TestNestJSResp, err error) {
	// 通过Nacos服务发现调用NestJS服务
	opts := client.RequestOptions{
		Method: http.MethodGet,
	}
	sd := client.NewServiceDiscovery(l.svcCtx.NamingClient)
	result, err := sd.CallService(l.ctx, "nestjs", "/api_nestjs/nestjs", opts)
	if err != nil {
		l.Error(fmt.Sprintf(utils.PARSE_ERR+": %v", err))
		panic(exceptions.NewBusinessError(utils.PARSE_ERR, err.Error()))
	}

	resultData := result.Data.(string)
	resp = &types.TestNestJSResp{
		Data: resultData,
	}

	return
}
