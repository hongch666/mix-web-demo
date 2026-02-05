import { Controller, Get } from '@nestjs/common';
import type { EventLoopMetrics } from './monitor.service';
import { MonitorService } from './monitor.service';
import { ApiTags, ApiOperation } from '@nestjs/swagger';

@ApiTags('性能监测')
@Controller('api/monitor')
export class MonitorController {
  constructor(private monitorService: MonitorService) {}

  @Get('eventloop-metrics')
  @ApiOperation({ summary: '获取 EventLoop 延迟指标' })
  getEventLoopMetrics(): EventLoopMetrics {
    return this.monitorService.getMetrics();
  }

  @Get('clear-metrics')
  @ApiOperation({ summary: '清空指标数据' })
  clearMetrics() {
    this.monitorService.clearMetrics();
    return { message: '指标数据已清空' };
  }
}
