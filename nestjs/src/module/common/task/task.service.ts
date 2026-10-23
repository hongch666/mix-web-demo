import { Injectable } from "@nestjs/common";
import { Cron } from "@nestjs/schedule";
import { trace } from "@opentelemetry/api";
import { Defaults, Messages, RedisKeys } from "src/common/constants";
import { LoggerService } from "src/module/common/logger/logger.service";
import { taskDuration, taskRuns } from "../telemetry/metrics";
import { ApiLogService } from "src/module/system/apiLog/apiLog.service";
import { RedisService } from "../redis/redis.service";

/**
 * 定时任务服务，通过 Cron 定时并配合 Redis 分布式锁清理过期的 API 日志与文章日志
 */
@Injectable()
export class TaskService {
  constructor(
    private readonly apiLogService: ApiLogService,
    private readonly redisService: RedisService,
    private readonly logger: LoggerService,
  ) {}

  /**
   * 每天凌晨2点执行的调度入口，负责分布式锁获取与释放、运行次数与耗时指标等后台处理，并调用日志清理逻辑
   * Cron 表达式: 秒 分 时 日 月 星期
   * '0 0 2 * * *' = 每天凌晨2点，频率提高后单次清理量小，且错过单次窗口仅影响一天
   * Service 层分批删除，锁过期时间只需覆盖单日清理时长
   * 使用 Redis 分布式锁，保证多实例部署时只有一个实例执行
   */
  @Cron("0 0 2 * * *")
  async cleanupOldApiLogs(): Promise<void> {
    // 定时任务没有请求入口，手动开启一段根 span，让本次执行的日志关联到同一个 trace_id
    await trace
      .getTracer(Defaults.OTEL_TRACER_NAME)
      .startActiveSpan("job:api-log-cleanup", async (span) => {
        try {
          await this.runCleanupWithLock();
        } catch (error: unknown) {
          span.recordException(error as Error);
          throw error;
        } finally {
          span.end();
        }
      });
  }

  /**
   * 清理任务的完整流程：分布式锁获取与释放、运行次数与耗时指标、锁相关日志
   */
  private async runCleanupWithLock(): Promise<void> {
    const lockKey = RedisKeys.LOCK_TASK_API_LOG_CLEANUP;
    const lockExpire = Defaults.LOCK_TASK_API_LOG_CLEANUP_EXPIRE;

    // 尝试获取分布式锁
    const lockValue = await this.redisService.tryLock(lockKey, lockExpire);
    if (lockValue === null) {
      // 获取锁失败，其他实例正在执行
      this.logger.info(Messages.REDIS_LOCK_ACQUIRE_FAIL.replace("%s", lockKey));
      return;
    }
    this.logger.info(
      Messages.REDIS_LOCK_ACQUIRE_SUCCESS.replace("%s", lockKey),
    );
    const startedAt: bigint = process.hrtime.bigint();
    let result: string = "success";

    try {
      await this.executeApiLogCleanup();
    } catch (error: unknown) {
      result = "failure";
      const errorMessage: string =
        error instanceof Error ? error.message : String(error);
      this.logger.error(Messages.API_LOG_CLEANUP_FAILED(errorMessage));
    } finally {
      taskRuns.labels("api-log-cleanup", result).inc();
      taskDuration
        .labels("api-log-cleanup")
        .observe(Number(process.hrtime.bigint() - startedAt) / 1_000_000_000);
      const released = await this.redisService.unlock(lockKey, lockValue);
      if (released) {
        this.logger.info(
          Messages.REDIS_LOCK_RELEASE_SUCCESS.replace("%s", lockKey),
        );
      } else {
        this.logger.info(
          Messages.REDIS_LOCK_RELEASE_FAIL.replace("%s", lockKey),
        );
      }
    }
  }

  /**
   * 手动触发一次 API 日志清理任务，供控制器调用
   * 完整任务流程在后台异步执行，不等待完成，异常兜底记录日志避免未处理的 Promise 拒绝
   */
  async triggerApiLogCleanup(): Promise<void> {
    void this.cleanupOldApiLogs().catch((error: unknown) => {
      const errorMessage: string =
        error instanceof Error ? error.message : String(error);
      this.logger.error(Messages.API_LOG_CLEANUP_FAILED(errorMessage));
    });
  }

  /**
   * API 日志清理的业务逻辑，按保留期限计算过期时间点并分批删除过期日志，由定时调度入口调用
   */
  async executeApiLogCleanup(): Promise<void> {
    this.logger.info(Messages.TASK_CLEAN);

    // 计算保留期限对应的过期时间点
    const expireBefore: Date = new Date();
    expireBefore.setMonth(
      expireBefore.getMonth() - Defaults.LOG_RETENTION_MONTHS,
    );

    // 通过 ApiLogService 清理日志（不再直接操作 Model，消除跨层引用）
    const deletedCount: number =
      await this.apiLogService.cleanupOldLogs(expireBefore);

    this.logger.info(Messages.API_LOG_CLEANUP_COMPLETED(deletedCount));
  }
}
