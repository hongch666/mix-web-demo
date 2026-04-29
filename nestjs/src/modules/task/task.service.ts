import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Cron } from '@nestjs/schedule';
import { Model } from 'mongoose';
import { ApiLog, ApiLogDocument } from 'src/api/apiLog/schema/apiLog.schema';
import { Constants } from '../../common/utils/constants';
import { logger } from '../../common/utils/writeLog';
import { RedisService } from '../redis/redis.service';

interface DeleteResult {
  deletedCount: number;
}

@Injectable()
export class TaskService {
  constructor(
    @InjectModel(ApiLog.name)
    private readonly apiLogModel: Model<ApiLogDocument>,
    private readonly redisService: RedisService,
  ) {}

  /**
   * 每月1日凌晨2点执行，删除超过1个月的API日志
   * Cron 表达式: 秒 分 时 日 月 星期
   * '0 0 2 1 * *' = 每月1日凌晨2点
   * 使用 Redis 分布式锁，保证多实例部署时只有一个实例执行
   */
  @Cron('0 0 2 1 * *')
  async cleanupOldApiLogs(): Promise<void> {
    const lockKey = Constants.LOCK_TASK_API_LOG_CLEANUP;
    const lockExpire = Constants.LOCK_TASK_API_LOG_CLEANUP_EXPIRE;

    // 尝试获取分布式锁
    const lockValue = await this.redisService.tryLock(lockKey, lockExpire);
    if (lockValue === null) {
      // 获取锁失败，其他实例正在执行
      logger.info(Constants.REDIS_LOCK_ACQUIRE_FAIL.replace('%s', lockKey));
      return;
    }
    logger.info(Constants.REDIS_LOCK_ACQUIRE_SUCCESS.replace('%s', lockKey));

    try {
      logger.info(Constants.TASK_CLEAN);

      // 计算1个月前的日期
      const oneMonthAgo: Date = new Date();
      oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);

      // 删除超过1个月的日志
      const result: DeleteResult = await this.apiLogModel
        .deleteMany({
          createdAt: { $lt: oneMonthAgo },
        })
        .exec();

      logger.info(
        `API 日志清理完成，删除了 ${result.deletedCount} 条超过1个月的日志`,
      );
    } catch (error: unknown) {
      const errorMessage: string =
        error instanceof Error ? error.message : String(error);
      logger.error(`清理 API 日志失败: ${errorMessage}`);
    } finally {
      const released = await this.redisService.unlock(lockKey, lockValue);
      if (released) {
        logger.info(Constants.REDIS_LOCK_RELEASE_SUCCESS.replace('%s', lockKey));
      } else {
        logger.info(Constants.REDIS_LOCK_RELEASE_FAIL.replace('%s', lockKey));
      }
    }
  }
}
