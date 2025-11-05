import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Cron } from '@nestjs/schedule';
import { Model } from 'mongoose';
import { ArticleLog, ArticleLogDocument } from 'src/api/log/schema/log.schema';
import { ApiLog, ApiLogDocument } from 'src/api/api-log/schema/api-log.schema';
import { fileLogger } from '../utils/writeLog';

@Injectable()
export class TaskService {
  constructor(
    @InjectModel(ArticleLog.name)
    private readonly logModel: Model<ArticleLogDocument>,
    @InjectModel(ApiLog.name)
    private readonly apiLogModel: Model<ApiLogDocument>,
  ) {}

  /**
   * 每月1日凌晨0点执行，清除文章操作日志
   * Cron 表达式: 秒 分 时 日 月 星期
   * '0 0 1 * *' = 每月1日凌晨0点
   */
  @Cron('0 0 1 * *')
  async handleCronWithCustomExpression() {
    fileLogger.info('开始清除任务');
    const result = await this.logModel.deleteMany({}).exec();
    fileLogger.info(`清除任务完成，删除了 ${result.deletedCount} 条日志`);
  }

  /**
   * 每月1日凌晨2点执行，删除超过1个月的API日志
   * Cron 表达式: 秒 分 时 日 月 星期
   * '0 0 2 1 * *' = 每月1日凌晨2点
   */
  @Cron('0 0 2 1 * *')
  async cleanupOldApiLogs() {
    try {
      fileLogger.info('开始清理超过1个月的 API 日志');

      // 计算1个月前的日期
      const oneMonthAgo = new Date();
      oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);

      // 删除超过1个月的日志
      const result = await this.apiLogModel
        .deleteMany({
          createdAt: { $lt: oneMonthAgo },
        })
        .exec();

      fileLogger.info(
        `API 日志清理完成，删除了 ${result.deletedCount} 条超过1个月的日志`,
      );
    } catch (error) {
      fileLogger.error(`清理 API 日志失败: ${error.message}`);
    }
  }
}
