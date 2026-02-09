import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Cron } from '@nestjs/schedule';
import { Model } from 'mongoose';
import { ApiLog, ApiLogDocument } from 'src/api/api-log/schema/api-log.schema';
import { logger } from '../../common/utils/writeLog';
import { Constants } from '../../common/utils/constants';

interface DeleteResult {
  deletedCount: number;
}

@Injectable()
export class TaskService {
  constructor(
    @InjectModel(ApiLog.name)
    private readonly apiLogModel: Model<ApiLogDocument>,
  ) {}

  /**
   * 每月1日凌晨2点执行，删除超过1个月的API日志
   * Cron 表达式: 秒 分 时 日 月 星期
   * '0 0 2 1 * *' = 每月1日凌晨2点
   */
  @Cron('0 0 2 1 * *')
  async cleanupOldApiLogs(): Promise<void> {
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
    }
  }
}
