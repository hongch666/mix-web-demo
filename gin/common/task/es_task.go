package task

import (
	"fmt"
	"gin_proj/common/syncer"
	"gin_proj/common/utils"

	"github.com/robfig/cron/v3"
)

var TaskScheduler *cron.Cron

func InitTasks() {
	TaskScheduler = cron.New()

	// 每 30 分钟同步一次 ES
	_, err := TaskScheduler.AddFunc("*/30 * * * *", func() {
		utils.FileLogger.Info("[定时任务] 开始同步文章到 Elasticsearch")
		syncer.SyncArticlesToES()
		utils.FileLogger.Info("[定时任务] 同步成功")
	})

	if err != nil {
		utils.FileLogger.Error(fmt.Sprintf("[定时任务] 注册同步任务失败：%v", err))
	}

	TaskScheduler.Start()
	utils.FileLogger.Info("[定时任务] 已启动")
}
