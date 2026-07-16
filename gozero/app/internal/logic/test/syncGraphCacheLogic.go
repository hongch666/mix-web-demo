package test

import (
	"context"
	"fmt"

	"app/common/constants"
	"app/common/exceptions"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/task/logic"
	"app/internal/types"
)

type SyncGraphCacheLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

func NewSyncGraphCacheLogic(ctx context.Context, svcCtx *svc.ServiceContext) *SyncGraphCacheLogic {
	return &SyncGraphCacheLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

func (l *SyncGraphCacheLogic) SyncGraphCache(req *types.SyncGraphCacheReq) (resp *types.SyncGraphCacheResp, err error) {
	l.Info(constants.TASK_GRAPH_CACHE_MANUAL_START)

	if err = logic.SyncGraphFeaturesToRedis(l.ctx, l.svcCtx); err != nil {
		l.Error(fmt.Sprintf("%s: %v", constants.TASK_GRAPH_CACHE_MANUAL_FAIL, err))
		return nil, exceptions.NewInternalServerError(constants.TASK_GRAPH_CACHE_MANUAL_FAIL, err.Error())
	}

	l.Info(constants.TASK_GRAPH_CACHE_MANUAL_DONE)
	return &types.SyncGraphCacheResp{}, nil
}
