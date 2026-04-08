package task

import (
	"fmt"

	"app/common/utils"
	"app/internal/svc"
	"app/internal/task/logic"

	"github.com/robfig/cron/v3"
)

var TaskScheduler *cron.Cron

// InitTaskScheduler 初始化任务调度器
func InitTaskScheduler(svcCtx *svc.ServiceContext) {
	TaskScheduler = cron.New()

	// 每天同步一次 ES
	_, err := TaskScheduler.AddFunc("* * */1 * *", func() {
		if svcCtx.Logger != nil {
			svcCtx.Logger.Info(utils.TASK_SYNC_ES_STARTED_MESSAGE)
		}
		if err := logic.SyncArticlesToES(svcCtx); err != nil {
			if svcCtx.Logger != nil {
				svcCtx.Logger.Error(fmt.Sprintf(utils.TASK_SYNC_ES_FAILED_MESSAGE, err))
			}
			return
		}
		if svcCtx.Logger != nil {
			svcCtx.Logger.Info(utils.TASK_SYNC_ES_COMPLETED_MESSAGE)
		}
	})
	if err != nil {
		if svcCtx.Logger != nil {
			svcCtx.Logger.Error(fmt.Sprintf(utils.TASK_SYNC_ES_FAILED_MESSAGE, err))
		}
	}

	TaskScheduler.Start()
	if svcCtx.Logger != nil {
		svcCtx.Logger.Info(utils.TASK_SCHEDULER_STARTED_MESSAGE)
	}
}
