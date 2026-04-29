package task

import (
	"context"
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
		ctx := context.Background()
		lockKey := utils.LOCK_TASK_ES_SYNC

		// 尝试获取分布式锁
		if svcCtx.RedisClient == nil {
			// Redis 未配置，直接执行（单实例模式）
			executeESSync(ctx, svcCtx)
			return
		}

		lock := utils.NewRedisDistributedLock(svcCtx.RedisClient)
		lockValue, err := lock.TryLock(ctx, lockKey, utils.LOCK_TASK_ES_SYNC_EXPIRE)
		if err != nil {
			if svcCtx.Logger != nil {
				svcCtx.Logger.Error(fmt.Sprintf(utils.REDIS_LOCK_ACQUIRE_ERROR, err))
			}
			return
		}
		if lockValue == "" {
			if svcCtx.Logger != nil {
				svcCtx.Logger.Info(fmt.Sprintf(utils.REDIS_LOCK_ACQUIRE_FAIL, lockKey))
			}
			return
		}
		if svcCtx.Logger != nil {
			svcCtx.Logger.Info(fmt.Sprintf(utils.REDIS_LOCK_ACQUIRE_SUCCESS, lockKey))
		}

		// 确保任务执行完毕后释放锁
		defer func() {
			released, unlockErr := lock.Unlock(ctx, lockKey, lockValue)
			if unlockErr != nil {
				if svcCtx.Logger != nil {
					svcCtx.Logger.Error(fmt.Sprintf(utils.REDIS_LOCK_RELEASE_ERROR, unlockErr))
				}
				return
			}
			if released {
				if svcCtx.Logger != nil {
					svcCtx.Logger.Info(fmt.Sprintf(utils.REDIS_LOCK_RELEASE_SUCCESS, lockKey))
				}
			} else {
				if svcCtx.Logger != nil {
					svcCtx.Logger.Info(fmt.Sprintf(utils.REDIS_LOCK_RELEASE_FAIL, lockKey))
				}
			}
		}()

		executeESSync(ctx, svcCtx)
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

// executeESSync 执行 ES 同步任务
func executeESSync(ctx context.Context, svcCtx *svc.ServiceContext) {
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
}
