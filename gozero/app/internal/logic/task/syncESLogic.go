// Code scaffolded by goctl. Safe to edit.
// goctl 1.9.2

package task

import (
	"context"
	"fmt"

	"app/common/constants"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/task/logic"
	"app/internal/types"
)

type SyncESLogic struct {
	ctx    context.Context
	svcCtx *svc.ServiceContext
	*utils.ZeroLogger
}

// 手动触发同步ES任务
func NewSyncESLogic(ctx context.Context, svcCtx *svc.ServiceContext) *SyncESLogic {
	return &SyncESLogic{
		ctx:        ctx,
		svcCtx:     svcCtx,
		ZeroLogger: svcCtx.Logger.WithContext(ctx),
	}
}

func (l *SyncESLogic) SyncES(req *types.SyncESReq) (resp *types.SyncESResp, err error) {
	l.Info(constants.TASK_SYNC_ES_STARTED_MESSAGE)

	// 在后台 goroutine 中异步执行 ES 同步，立刻返回成功
	go func() {
		if syncErr := logic.SyncArticlesToES(context.Background(), l.svcCtx); syncErr != nil {
			l.Error(fmt.Sprintf("%s: %v", constants.TASK_SYNC_ES_FAILED_MESSAGE, syncErr))
			return
		}
		l.Info(constants.TASK_SYNC_ES_COMPLETED_MESSAGE)
	}()

	return &types.SyncESResp{}, nil
}
