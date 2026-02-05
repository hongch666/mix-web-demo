package task

import (
	"fmt"

	"github.com/hongch666/mix-web-demo/gin/common/task/logic"
	"github.com/hongch666/mix-web-demo/gin/common/utils"

	"github.com/robfig/cron/v3"
)

var TaskScheduler *cron.Cron

func init() {
	TaskScheduler = cron.New()

	// 每5分钟同步一次 ES
	_, err := TaskScheduler.AddFunc("*/5 * * * *", func() {
		utils.Log.Info(utils.TASK_SYNC_ES_STARTED_MESSAGE)
		logic.SyncArticlesToES()
		utils.Log.Info(utils.TASK_SYNC_ES_COMPLETED_MESSAGE)
	})

	if err != nil {
		utils.Log.Error(fmt.Sprintf(utils.TASK_SYNC_ES_FAILED_MESSAGE, err))
	}

	TaskScheduler.Start()
	utils.Log.Info(utils.TASK_SCHEDULER_STARTED_MESSAGE)
}
