import { Module } from "@nestjs/common";
import { ApiLogModule } from "src/module/system/apiLog/apiLog.module";
import { ArticleLogModule } from "src/module/system/articleLog/articleLog.module";
import { TaskController } from "./task.controller";
import { TaskService } from "./task.service";

/**
 * 定时任务模块，注册任务控制器与服务，聚合 API 日志与文章日志清理能力
 */
@Module({
  imports: [ArticleLogModule, ApiLogModule],
  controllers: [TaskController],
  providers: [TaskService],
  exports: [TaskService],
})
export class TaskModule {}
