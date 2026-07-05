import { Controller, Get, Post } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { Constants } from 'src/common/utils/constants';
import { ApiResponse, success } from 'src/common/utils/response';
import { ApiLog } from 'src/framework/decorators/apiLog.decorator';
import { RequireInternalToken } from 'src/framework/decorators/requireInternalToken.decorator';
import { FastapiClientService } from 'src/module/common/client/fastapiClient.service';
import { GoZeroClientService } from 'src/module/common/client/gozeroClient.service';
import { SpringClientService } from 'src/module/common/client/springClient.service';
import { TaskService } from 'src/module/common/task/task.service';

@Controller('api_nestjs')
@ApiTags('测试模块')
export class TestController {
  constructor(
    private readonly springClientService: SpringClientService,
    private readonly gozeroClientService: GoZeroClientService,
    private readonly fastapiClientService: FastapiClientService,
    private readonly taskService: TaskService,
  ) {}

  @Get('nestjs')
  @ApiOperation({
    summary: 'NestJS自己的测试',
    description: '输出欢迎信息',
  })
  @ApiLog('测试NestJS服务')
  async getNestjs(): Promise<ApiResponse<string>> {
    return success(Constants.TEST_WELCOME);
  }

  @Get('spring')
  @ApiOperation({
    summary: '调用Spring的测试',
    description: '输出欢迎信息',
  })
  @ApiLog('测试Spring服务')
  async getSpring(): Promise<ApiResponse<unknown>> {
    const res: Record<string, unknown> = await this.springClientService.test();
    return success(res.data);
  }

  @Get('gozero')
  @ApiOperation({
    summary: '调用GoZero的测试',
    description: '输出欢迎信息',
  })
  @ApiLog('测试GoZero服务')
  async getGin(): Promise<ApiResponse<unknown>> {
    const res: Record<string, unknown> = await this.gozeroClientService.test();
    return success(res.data);
  }

  @Get('fastapi')
  @ApiOperation({
    summary: '调用FastAPI的测试',
    description: '输出欢迎信息',
  })
  @ApiLog('测试FastAPI服务')
  async getFastAPI(): Promise<ApiResponse<unknown>> {
    const res: Record<string, unknown> = await this.fastapiClientService.test();
    return success(res.data);
  }

  @Post('execute/apilog')
  @ApiOperation({
    summary: '手动执行清理API日志任务',
    description: '手动触发清理超过1个月的API日志任务',
  })
  @RequireInternalToken()
  @ApiLog('手动执行清理API日志任务')
  async executeCleanupOldApiLogsTask(): Promise<ApiResponse<null>> {
    await this.taskService.cleanupOldApiLogs();
    return success(null);
  }

  @Post('execute/articlelog')
  @ApiOperation({
    summary: '手动执行清理文章日志任务',
    description: '手动触发清理超过1个月的文章日志任务',
  })
  @RequireInternalToken()
  @ApiLog('手动执行清理文章日志任务')
  async executeCleanupOldArticleLogsTask(): Promise<ApiResponse<null>> {
    await this.taskService.cleanupOldArticleLogs();
    return success(null);
  }
}
