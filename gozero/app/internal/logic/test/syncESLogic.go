// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package test

import (
	"context"
	"fmt"

	"app/common/logger"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/task/logic"
	"app/internal/types"
)

type SyncESLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*logger.ZeroLogger
}

// 手动触发同步ES任务
func NewSyncESLogic(ctx context.Context, svcCtx *svc.ServiceContext) *SyncESLogic {
	return &SyncESLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger,
	}
}

func (l *SyncESLogic) SyncES(req *types.SyncESReq) (resp *types.SyncESResp, err error) {
	// 手动触发同步ES任务
	l.Info(utils.TASK_SYNC_ES_STARTED_MESSAGE)

	// 调用实际的ES同步逻辑
	if err = logic.SyncArticlesToES(l.svcCtx); err != nil {
		l.Error(fmt.Sprintf("%s: %v", utils.TASK_SYNC_ES_FAILED_MESSAGE, err))
		return nil, err
	}

	l.Info(utils.TASK_SYNC_ES_COMPLETED_MESSAGE)

	return
}
