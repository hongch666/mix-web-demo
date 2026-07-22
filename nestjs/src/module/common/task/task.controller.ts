import { Controller, Post } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import { ApiResponse, success } from "src/common/utils/response";
import { ApiLog } from "src/framework/decorators/apiLog.decorator";
import { RequireInternalToken } from "src/framework/decorators/requireInternalToken.decorator";
import { TaskService } from "./task.service";

@Controller("task")
@ApiTags("定时任务模块")
export class TaskController {
  constructor(private readonly taskService: TaskService) {}

  @Post("apilog")
  @ApiOperation({
    summary: "手动执行清理API日志任务",
    description: "手动触发清理超过1个月的API日志任务",
  })
  @RequireInternalToken()
  @ApiLog("手动执行清理API日志任务")
  async executeCleanupOldApiLogsTask(): Promise<ApiResponse<null>> {
    // 后台异步执行，不阻塞接口响应
    void this.taskService.cleanupOldApiLogs();
    return success(null);
  }

  @Post("articlelog")
  @ApiOperation({
    summary: "手动执行清理文章日志任务",
    description: "手动触发清理超过1个月的文章日志任务",
  })
  @RequireInternalToken()
  @ApiLog("手动执行清理文章日志任务")
  async executeCleanupOldArticleLogsTask(): Promise<ApiResponse<null>> {
    // 后台异步执行，不阻塞接口响应
    void this.taskService.cleanupOldArticleLogs();
    return success(null);
  }
}
