import { Module } from "@nestjs/common";
import { ApiLogModule } from "src/module/system/apiLog/apiLog.module";
import { ArticleLogModule } from "src/module/system/articleLog/articleLog.module";
import { TaskService } from "./task.service";

@Module({
  imports: [ArticleLogModule, ApiLogModule],
  providers: [TaskService],
  exports: [TaskService],
})
export class TaskModule {}
