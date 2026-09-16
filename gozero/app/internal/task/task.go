package task

import (
	"context"
	"fmt"
	"time"

	"app/common/constants"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/task/logic"

	"github.com/robfig/cron/v3"
)

// NewTaskScheduler 创建并启动定时任务调度器，由调用方挂到 ServiceContext 上
func NewTaskScheduler(svcCtx *svc.ServiceContext) *cron.Cron {
	scheduler := cron.New()

	// 每小时同步一次 ES
	_, err := scheduler.AddFunc("0 * * * *", func() {
		ctx, cancel := context.WithTimeout(svcCtx.Context, 30*time.Minute)
		defer cancel()
		logger := svcCtx.Logger.WithContext(ctx)
		lockKey := constants.LOCK_TASK_ES_SYNC

		// 尝试获取分布式锁
		if svcCtx.RedisClient == nil {
			// Redis 未配置时无法保证分布式互斥，跳过本次任务
			logger.Info(fmt.Sprintf(constants.REDIS_LOCK_ACQUIRE_FAIL, lockKey))
			return
		}

		lock := utils.NewRedisDistributedLock(svcCtx.RedisClient)
		lockValue, err := lock.TryLock(ctx, lockKey, constants.LOCK_TASK_ES_SYNC_EXPIRE)
		if err != nil {
			logger.Error(fmt.Sprintf(constants.REDIS_LOCK_ACQUIRE_ERROR, err))
			return
		}
		if lockValue == "" {
			logger.Info(fmt.Sprintf(constants.REDIS_LOCK_ACQUIRE_FAIL, lockKey))
			return
		}
		logger.Info(fmt.Sprintf(constants.REDIS_LOCK_ACQUIRE_SUCCESS, lockKey))

		// 确保任务执行完毕后释放锁
		defer func() {
			released, unlockErr := lock.Unlock(ctx, lockKey, lockValue)
			if unlockErr != nil {
				logger.Error(fmt.Sprintf(constants.REDIS_LOCK_RELEASE_ERROR, unlockErr))
				return
			}
			if released {
				logger.Info(fmt.Sprintf(constants.REDIS_LOCK_RELEASE_SUCCESS, lockKey))
			} else {
				logger.Info(fmt.Sprintf(constants.REDIS_LOCK_RELEASE_FAIL, lockKey))
			}
		}()

		executeESSync(ctx, logger, svcCtx)
	})
	if err != nil {
		if svcCtx.Logger != nil {
			svcCtx.Logger.Error(fmt.Sprintf(constants.TASK_SYNC_ES_FAILED_MESSAGE, err))
		}
	}

	scheduler.Start()
	if svcCtx.Logger != nil {
		svcCtx.Logger.Info(constants.TASK_SCHEDULER_STARTED_MESSAGE)
	}
	return scheduler
}

// executeESSync 执行 ES 同步任务
func executeESSync(ctx context.Context, logger *utils.ZeroLogger, svcCtx *svc.ServiceContext) {
	logger.Info(constants.TASK_SYNC_ES_STARTED_MESSAGE)
	if err := logic.SyncArticlesToES(ctx, svcCtx); err != nil {
		logger.Error(fmt.Sprintf(constants.TASK_SYNC_ES_FAILED_MESSAGE, err))
		return
	}
	logger.Info(constants.TASK_SYNC_ES_COMPLETED_MESSAGE)
}
