import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { ApiLog, ApiLogSchema } from 'src/api/api-log/schema/api-log.schema';
import {
  ArticleLog,
  ArticleLogSchema,
} from 'src/api/article-log/schema/article-log.schema';
import { TaskService } from './task.service';

@Module({
  imports: [
    MongooseModule.forFeature([
      { name: ArticleLog.name, schema: ArticleLogSchema },
      { name: ApiLog.name, schema: ApiLogSchema },
    ]),
  ],
  providers: [TaskService],
  exports: [TaskService],
})
export class TaskModule {}
