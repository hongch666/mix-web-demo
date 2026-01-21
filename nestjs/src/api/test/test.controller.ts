import { Controller, Get, Post } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { ApiLog } from 'src/common/decorators/api-log.decorator';
import { NacosService } from 'src/modules/nacos/nacos.service';
import { TaskService } from 'src/modules/task/task.service';
import { success } from 'src/common/utils/response';

@Controller('api_nestjs')
@ApiTags('测试模块')
export class TestController {
  constructor(
    private readonly nacosService: NacosService,
    private readonly taskServicce: TaskService,
  ) {}

  @Get('nestjs')
  @ApiOperation({
    summary: 'NestJS自己的测试',
    description: '输出欢迎信息',
  })
  @ApiLog('测试NestJS服务')
  async getNestjs(): Promise<any> {
    return success('Hello,I am Nest.js!');
  }

  @Get('spring')
  @ApiOperation({
    summary: '调用Spring的测试',
    description: '输出欢迎信息',
  })
  @ApiLog('测试Spring服务')
  async getSpring(): Promise<any> {
    const res = await this.nacosService.call({
      serviceName: 'spring',
      method: 'GET',
      path: '/api_spring/spring',
    });
    return success(res.data);
  }

  @Get('gin')
  @ApiOperation({
    summary: '调用Gin的测试',
    description: '输出欢迎信息',
  })
  @ApiLog('测试Gin服务')
  async getGin(): Promise<any> {
    const res = await this.nacosService.call({
      serviceName: 'gin',
      method: 'GET',
      path: '/api_gin/gin',
    });
    return success(res.data);
  }

  @Get('fastapi')
  @ApiOperation({
    summary: '调用FastAPI的测试',
    description: '输出欢迎信息',
  })
  @ApiLog('测试FastAPI服务')
  async getFastAPI(): Promise<any> {
    const res = await this.nacosService.call({
      serviceName: 'fastapi',
      method: 'GET',
      path: '/api_fastapi/fastapi',
    });
    return success(res.data);
  }

  @Post('execute/apilog')
  @ApiOperation({
    summary: '手动执行清理API日志任务',
    description: '手动触发清理超过1个月的API日志任务',
  })
  @ApiLog('手动执行清理API日志任务')
  async executeCleanupOldApiLogsTask() {
    await this.taskServicce.cleanupOldApiLogs();
    return success(null);
  }
}
