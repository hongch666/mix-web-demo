import { Injectable } from "@nestjs/common";
import { Cron } from "@nestjs/schedule";
import { Defaults, InfraKeys, Messages } from "src/common/constants";
import { logger } from "src/common/utils/writeLog";
import { ApiLogService } from "src/module/system/apiLog/apiLog.service";
import { ArticleLogService } from "src/module/system/articleLog/articleLog.service";
import { RedisService } from "../redis/redis.service";

@Injectable()
export class TaskService {
  constructor(
    private readonly apiLogService: ApiLogService,
    private readonly articleLogService: ArticleLogService,
    private readonly redisService: RedisService,
  ) {}

  /**
   * 每月1日凌晨2点执行，删除超过1个月的API日志
   * Cron 表达式: 秒 分 时 日 月 星期
   * '0 0 2 1 * *' = 每月1日凌晨2点
   * 使用 Redis 分布式锁，保证多实例部署时只有一个实例执行
   */
  @Cron("0 0 2 1 * *")
  async cleanupOldApiLogs(): Promise<void> {
    const lockKey = InfraKeys.LOCK_TASK_API_LOG_CLEANUP;
    const lockExpire = Defaults.LOCK_TASK_API_LOG_CLEANUP_EXPIRE;

    // 尝试获取分布式锁
    const lockValue = await this.redisService.tryLock(lockKey, lockExpire);
    if (lockValue === null) {
      // 获取锁失败，其他实例正在执行
      logger.info(Messages.REDIS_LOCK_ACQUIRE_FAIL.replace("%s", lockKey));
      return;
    }
    logger.info(Messages.REDIS_LOCK_ACQUIRE_SUCCESS.replace("%s", lockKey));

    try {
      logger.info(Messages.TASK_CLEAN);

      // 计算1个月前的日期
      const oneMonthAgo: Date = new Date();
      oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);

      // 通过 ApiLogService 清理日志（不再直接操作 Model，消除跨层引用）
      const deletedCount: number =
        await this.apiLogService.cleanupOldLogs(oneMonthAgo);

      logger.info(Messages.API_LOG_CLEANUP_COMPLETED(deletedCount));
    } catch (error: unknown) {
      const errorMessage: string =
        error instanceof Error ? error.message : String(error);
      logger.error(Messages.API_LOG_CLEANUP_FAILED(errorMessage));
    } finally {
      const released = await this.redisService.unlock(lockKey, lockValue);
      if (released) {
        logger.info(Messages.REDIS_LOCK_RELEASE_SUCCESS.replace("%s", lockKey));
      } else {
        logger.info(Messages.REDIS_LOCK_RELEASE_FAIL.replace("%s", lockKey));
      }
    }
  }

  /**
   * 每月1日凌晨0点执行，删除超过1个月的文章日志
   * Cron 表达式: 秒 分 时 日 月 星期
   * '0 0 0 1 * *' = 每月1日凌晨0点
   * 使用 Redis 分布式锁，保证多实例部署时只有一个实例执行
   */
  @Cron("0 0 0 1 * *")
  async cleanupOldArticleLogs(): Promise<void> {
    const lockKey = InfraKeys.LOCK_TASK_ARTICLE_LOG_CLEANUP;
    const lockExpire = Defaults.LOCK_TASK_ARTICLE_LOG_CLEANUP_EXPIRE;

    // 尝试获取分布式锁
    const lockValue = await this.redisService.tryLock(lockKey, lockExpire);
    if (lockValue === null) {
      // 获取锁失败，其他实例正在执行
      logger.info(Messages.REDIS_LOCK_ACQUIRE_FAIL.replace("%s", lockKey));
      return;
    }
    logger.info(Messages.REDIS_LOCK_ACQUIRE_SUCCESS.replace("%s", lockKey));

    try {
      logger.info(Messages.TASK_ARTICLE_CLEAN);

      // 计算1个月前的日期
      const oneMonthAgo: Date = new Date();
      oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);

      // 通过 ArticleLogService 清理日志（不再直接操作 Model，消除跨层引用）
      const deletedCount: number =
        await this.articleLogService.cleanupOldLogs(oneMonthAgo);

      logger.info(Messages.ARTICLE_LOG_CLEANUP_COMPLETED(deletedCount));
    } catch (error: unknown) {
      const errorMessage: string =
        error instanceof Error ? error.message : String(error);
      logger.error(Messages.ARTICLE_LOG_CLEANUP_FAILED(errorMessage));
    } finally {
      const released = await this.redisService.unlock(lockKey, lockValue);
      if (released) {
        logger.info(Messages.REDIS_LOCK_RELEASE_SUCCESS.replace("%s", lockKey));
      } else {
        logger.info(Messages.REDIS_LOCK_RELEASE_FAIL.replace("%s", lockKey));
      }
    }
  }
}
