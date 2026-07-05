import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import {
  ApiLog,
  ApiLogSchema,
} from 'src/module/system/apiLog/schema/apiLog.schema';
import {
  ArticleLog,
  ArticleLogSchema,
} from 'src/module/system/articleLog/schema/articleLog.schema';
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
