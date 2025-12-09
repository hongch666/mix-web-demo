import { Module } from '@nestjs/common';
import { TaskService } from './task.service';
import { MongooseModule } from '@nestjs/mongoose';
import { ArticleLog, ArticleLogSchema } from 'src/api/log/schema/log.schema';
import { ApiLog, ApiLogSchema } from 'src/api/api-log/schema/api-log.schema';

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
