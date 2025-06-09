package task

import (
	"gin_proj/syncer"
	"log"

	"github.com/robfig/cron/v3"
)

var TaskScheduler *cron.Cron

func InitTasks() {
	TaskScheduler = cron.New()

	// 每 10 分钟同步一次 ES
	_, err := TaskScheduler.AddFunc("*/10 * * * *", func() {
		log.Println("[定时任务] 开始同步文章到 Elasticsearch")
		if err := syncer.SyncArticlesToES(); err != nil {
			log.Println("[定时任务] 同步失败：", err)
		} else {
			log.Println("[定时任务] 同步成功")
		}
	})

	if err != nil {
		log.Fatalln("注册定时任务失败：", err)
	}

	TaskScheduler.Start()
	log.Println("[定时任务] 已启动")
}
