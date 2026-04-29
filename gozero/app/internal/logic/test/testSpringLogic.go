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
	// 通过Nacos服务发现调用Spring服务
	opts := client.RequestOptions{
		Method: http.MethodGet,
	}
	sd := client.NewServiceDiscovery(l.svcCtx.NamingClient)
	result, err := sd.CallService(l.ctx, "spring", "/api_spring/spring", opts)
	if err != nil {
		l.Error(fmt.Sprintf(utils.PARSE_ERR+": %v", err))
		panic(exceptions.NewBusinessError(utils.PARSE_ERR, err.Error()))
	}

	resultData := result.Data.(string)
	resp = &types.TestSpringResp{
		Data: resultData,
	}

	return
}
