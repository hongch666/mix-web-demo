// Code scaffolded by goctl. Safe to edit.

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

// syncArticleESChangesFunc 后台同步实现，抽为变量便于单元测试注入替身
var syncArticleESChangesFunc = logic.SyncArticleESChanges

// runSyncInBackground 后台执行方式，抽为变量便于单元测试控制执行时机与同步等待
var runSyncInBackground = func(l *SyncESLogic, task func()) {
	utils.SafeGo(l.ZeroLogger, constants.SAFE_GO_SYNC_ES_DATA, task)
}

func (l *SyncESLogic) SyncES(req *types.SyncESReq) (resp *types.SyncESResp, err error) {
	l.Info(constants.TASK_SYNC_ES_STARTED_MESSAGE)

	// 拷贝请求字段，避免后台 goroutine 引用请求对象
	changeType := req.ChangeType
	ids := append([]int64(nil), req.Ids...)

	// 在后台 goroutine 中异步执行 ES 同步，立刻返回成功
	// 携带主键时按主键精确同步，主键为空时退化为全量同步
	runSyncInBackground(l, func() {
		if syncErr := syncArticleESChangesFunc(l.svcCtx.Context, l.svcCtx, changeType, ids); syncErr != nil {
			l.Error(fmt.Sprintf("%s: %v", constants.TASK_SYNC_ES_FAILED_MESSAGE, syncErr))
			return
		}
		l.Info(constants.TASK_SYNC_ES_COMPLETED_MESSAGE)
	})

	return &types.SyncESResp{}, nil
}
