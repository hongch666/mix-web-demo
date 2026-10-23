import { Controller, Post } from "@nestjs/common";
import { ApiOperation, ApiTags } from "@nestjs/swagger";
import { ApiResponse, success } from "src/common/utils/response";
import {
  ApiResponseModel,
  SwaggerNullData,
} from "src/common/utils/swaggerResponse";
import { ApiLog } from "src/framework/decorators/apiLog.decorator";
import { RequireInternalToken } from "src/framework/decorators/requireInternalToken.decorator";
import { TaskService } from "./task.service";

/**
 * 定时任务模块控制器，供内部服务手动触发日志清理任务
 */
@Controller("task")
@ApiTags("定时任务模块")
export class TaskController {
  constructor(private readonly taskService: TaskService) {}

  /**
   * 手动触发清理超过3个月的 API 日志任务，后台异步执行并立即返回
   */
  @Post("apilog")
  @ApiOperation({
    summary: "手动执行清理API日志任务",
    description: "手动触发清理超过3个月的API日志任务",
  })
  @RequireInternalToken()
  @ApiLog("手动执行清理API日志任务")
  @ApiResponseModel({ data: SwaggerNullData })
  async executeCleanupOldApiLogsTask(): Promise<ApiResponse<null>> {
    // 交给服务层在后台异步执行，不阻塞接口响应
    await this.taskService.triggerApiLogCleanup();
    return success(null);
  }
}
