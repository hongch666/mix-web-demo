import { Injectable, Logger } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Cron, CronExpression } from '@nestjs/schedule';
import { Model } from 'mongoose';
import { ArticleLog, ArticleLogDocument } from 'src/api/log/schema/log.schema';
import { fileLogger } from '../utils/writeLog';

@Injectable()
export class TaskService {
  constructor(
    @InjectModel(ArticleLog.name)
    private readonly logModel: Model<ArticleLogDocument>,
  ) {}

  @Cron('0 0 * * * *')
  async handleCronWithCustomExpression() {
    fileLogger.info('开始清除任务');
    const result = await this.logModel.deleteMany({}).exec();
    fileLogger.info(`清除任务完成，删除了 ${result.deletedCount} 条日志`);
  }
}
