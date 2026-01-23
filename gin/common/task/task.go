package task

import (
	"fmt"
	"gin_proj/common/utils"

	"github.com/robfig/cron/v3"
)

var TaskScheduler *cron.Cron

func init() {
	TaskScheduler = cron.New()

	// 每5分钟同步一次 ES
	_, err := TaskScheduler.AddFunc("*/5 * * * *", func() {
		utils.FileLogger.Info(utils.TASK_SYNC_ES_STARTED_MESSAGE)
		SyncArticlesToES()
		utils.FileLogger.Info(utils.TASK_SYNC_ES_COMPLETED_MESSAGE)
	})

	if err != nil {
		utils.FileLogger.Error(fmt.Sprintf(utils.TASK_SYNC_ES_FAILED_MESSAGE, err))
	}

	TaskScheduler.Start()
	utils.FileLogger.Info(utils.TASK_SCHEDULER_STARTED_MESSAGE)
}
