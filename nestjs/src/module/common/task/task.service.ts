import { Injectable } from "@nestjs/common";
import { Cron } from "@nestjs/schedule";
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
   * 每天凌晨2点执行，删除超过3个月的API日志
   * Cron 表达式: 秒 分 时 日 月 星期
   * '0 0 2 * * *' = 每天凌晨2点，频率提高后单次清理量小，且错过单次窗口仅影响一天
   * Service 层分批删除，锁过期时间只需覆盖单日清理时长
   * 使用 Redis 分布式锁，保证多实例部署时只有一个实例执行
   */
  @Cron("0 0 2 * * *")
  async cleanupOldApiLogs(): Promise<void> {
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
}
