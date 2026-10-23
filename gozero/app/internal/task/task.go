package task

import (
	"context"
	"fmt"
	"time"

	"app/common/constants"
	"app/common/metrics"
	"app/common/utils"
	"app/internal/svc"
	"app/internal/task/logic"

	"github.com/redis/go-redis/v9"
	"github.com/robfig/cron/v3"
	zerotrace "github.com/zeromicro/go-zero/core/trace"
)

// 根据给定 Redis 客户端创建分布式锁实例的工厂函数类型
type RedisLockFactory func(*redis.Client) *utils.RedisDistributedLock

// TaskConfig 定时任务定义，新增任务只需在 NewTaskScheduler 中调用 addTask 注册
type TaskConfig struct {
	Name       string        // 任务名，用于监控指标标签
	Schedule   string        // cron 表达式
	LockKey    string        // 分布式锁 key
	LockExpire int64         // 锁过期时间（秒），应大于任务执行时间，防止死锁
	Timeout    time.Duration // 单次执行超时时间
	Run        TaskFunc      // 任务执行体，返回 error 表示本次执行失败
}

// TaskFunc 任务执行体函数签名
type TaskFunc func(ctx context.Context, logger *utils.ZeroLogger, svcCtx *svc.ServiceContext) error

// NewTaskScheduler 创建并启动定时任务调度器，由调用方挂到 ServiceContext 上
func NewTaskScheduler(svcCtx *svc.ServiceContext, lockFactory RedisLockFactory) *cron.Cron {
	scheduler := cron.New()

	// 每小时同步一次 ES
	addTask(scheduler, svcCtx, lockFactory, TaskConfig{
		Name:       "es-sync",
		Schedule:   "0 * * * *",
		LockKey:    constants.LOCK_TASK_ES_SYNC,
		LockExpire: constants.LOCK_TASK_ES_SYNC_EXPIRE,
		Timeout:    30 * time.Minute,
		Run:        executeESSync,
	})

	scheduler.Start()
	if svcCtx.Logger != nil {
		svcCtx.Logger.Info(constants.TASK_SCHEDULER_STARTED_MESSAGE)
	}
	return scheduler
}

// addTask 向调度器注册一个带分布式锁保护的定时任务
func addTask(scheduler *cron.Cron, svcCtx *svc.ServiceContext, lockFactory RedisLockFactory, cfg TaskConfig) {
	_, err := scheduler.AddFunc(cfg.Schedule, func() {
		runWithLock(svcCtx, lockFactory, cfg)
	})
	if err != nil && svcCtx.Logger != nil {
		svcCtx.Logger.Error(fmt.Sprintf(constants.TASK_REGISTER_FAILED_MESSAGE, cfg.Name, err))
	}
}

// runWithLock 以分布式锁保护的方式执行任务体：获取锁成功才执行，执行完毕释放锁并上报监控指标
func runWithLock(svcCtx *svc.ServiceContext, lockFactory RedisLockFactory, cfg TaskConfig) {
	ctx, cancel := context.WithTimeout(svcCtx.Context, cfg.Timeout)
	defer cancel()

	// 定时任务没有请求入口，手动开启一段根 span，让任务日志与内部调用关联到同一次执行
	// TracerFromContext 在上下文无 span 时回退到全局 tracer，OTel 关闭时自动退化为 noop
	tracer := zerotrace.TracerFromContext(ctx)
	ctx, span := tracer.Start(ctx, fmt.Sprintf("job:%s", cfg.Name))
	defer span.End()

	logger := svcCtx.Logger.WithContext(ctx)

	// Redis 未配置时无法保证分布式互斥，跳过本次任务
	if svcCtx.RedisClient == nil {
		logger.Info(fmt.Sprintf(constants.REDIS_LOCK_ACQUIRE_FAIL, cfg.LockKey))
		return
	}

	lock := lockFactory(svcCtx.RedisClient)
	lockValue, err := lock.TryLock(ctx, cfg.LockKey, cfg.LockExpire)
	if err != nil {
		logger.Error(fmt.Sprintf(constants.REDIS_LOCK_ACQUIRE_ERROR, err))
		return
	}
	if lockValue == "" {
		logger.Info(fmt.Sprintf(constants.REDIS_LOCK_ACQUIRE_FAIL, cfg.LockKey))
		return
	}
	logger.Info(fmt.Sprintf(constants.REDIS_LOCK_ACQUIRE_SUCCESS, cfg.LockKey))

	taskStartedAt := time.Now()
	taskResult := "success"
	defer func() {
		metrics.TaskRuns.WithLabelValues(cfg.Name, taskResult).Inc()
		metrics.TaskDuration.WithLabelValues(cfg.Name).Observe(time.Since(taskStartedAt).Seconds())
	}()

	// 确保任务执行完毕后释放锁
	defer func() {
		released, unlockErr := lock.Unlock(ctx, cfg.LockKey, lockValue)
		if unlockErr != nil {
			logger.Error(fmt.Sprintf(constants.REDIS_LOCK_RELEASE_ERROR, unlockErr))
			return
		}
		if released {
			logger.Info(fmt.Sprintf(constants.REDIS_LOCK_RELEASE_SUCCESS, cfg.LockKey))
		} else {
			logger.Info(fmt.Sprintf(constants.REDIS_LOCK_RELEASE_FAIL, cfg.LockKey))
		}
	}()

	if runErr := cfg.Run(ctx, logger, svcCtx); runErr != nil {
		taskResult = "failure"
	}
}

// executeESSync 执行 ES 同步任务
func executeESSync(ctx context.Context, logger *utils.ZeroLogger, svcCtx *svc.ServiceContext) error {
	logger.Info(constants.TASK_SYNC_ES_STARTED_MESSAGE)
	if err := logic.SyncArticlesToES(ctx, svcCtx); err != nil {
		logger.Error(fmt.Sprintf(constants.TASK_SYNC_ES_FAILED_MESSAGE, err))
		return err
	}
	logger.Info(constants.TASK_SYNC_ES_COMPLETED_MESSAGE)
	return nil
}
