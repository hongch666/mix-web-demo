package task

import (
	"fmt"
	"search/common/syncer"
	"search/common/utils"

	"github.com/robfig/cron/v3"
)

var TaskScheduler *cron.Cron

func InitTasks() {
	TaskScheduler = cron.New()

	// 每天同步一次 ES
	_, err := TaskScheduler.AddFunc("0 0 * * *", func() {
		utils.FileLogger.Info("[定时任务] 开始同步文章到 Elasticsearch")
		syncer.SyncArticlesToES(nil)
		utils.FileLogger.Info("[定时任务] 同步成功")
	})

	if err != nil {
		utils.FileLogger.Error(fmt.Sprintf("[定时任务] 注册同步任务失败：%v", err))
	}

	TaskScheduler.Start()
	utils.FileLogger.Info("[定时任务] 已启动")
}
