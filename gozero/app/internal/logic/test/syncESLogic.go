// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package test

import (
	"context"

	"app/common/task/logic"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/types"
)

type SyncESLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
}

// 手动触发同步ES任务
func NewSyncESLogic(ctx context.Context, svcCtx *svc.ServiceContext) *SyncESLogic {
	return &SyncESLogic{
		ctx:    ctx,
		svcCtx: svcCtx,
	}
}

func (l *SyncESLogic) SyncES(req *types.SyncESReq) (resp *types.SyncESResp, err error) {
	// 手动触发同步ES任务
	l.svcCtx.Logger.Info(utils.TASK_SYNC_ES_STARTED_MESSAGE)

	// 调用实际的ES同步逻辑
	logic.SyncArticlesToES(l.svcCtx)

	l.svcCtx.Logger.Info(utils.TASK_SYNC_ES_COMPLETED_MESSAGE)

	return
}
