import { Controller, Delete, Get, Param, Query } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { ApiLogService } from './api-log.service';
import { QueryApiLogDto } from './dto/api-log.dto';
import { ApiLog } from 'src/common/decorators/api-log.decorator';
import { RequireAdmin } from 'src/common/decorators/require-admin.decorator';

@Controller('api-logs')
@ApiTags('API日志模块')
export class ApiLogController {
  constructor(private readonly apiLogService: ApiLogService) {}

  /**
   * 查询API日志（分页）
   */
  @Get('list')
  @ApiOperation({
    summary: '查询API日志',
    description: '可根据用户ID、用户名、API路径等条件查询，支持分页',
  })
  @ApiLog('查询API日志')
  @RequireAdmin()
  async findByFilter(@Query() query: QueryApiLogDto) {
    return await this.apiLogService.findByFilter(query);
  }

  /**
   * 删除单条API日志
   */
  @Delete(':id')
  @ApiOperation({
    summary: '删除API日志',
    description: '通过日志ID删除单条日志',
  })
  @ApiLog('删除API日志')
  @RequireAdmin()
  async remove(@Param('id') id: string) {
    await this.apiLogService.removeById(id);
    return null;
  }

  /**
   * 批量删除API日志
   */
  @Delete('batch/:ids')
  @ApiOperation({
    summary: '批量删除API日志',
    description: '通过日志ID路径参数批量删除，多个ID用英文逗号分隔',
  })
  @ApiLog('批量删除API日志')
  @RequireAdmin()
  async removeByIds(@Param('ids') ids: string) {
    const idArr = ids
      .split(',')
      .map((id) => id.trim())
      .filter(Boolean);
    await this.apiLogService.removeByIds(idArr);
    return null;
  }
}
