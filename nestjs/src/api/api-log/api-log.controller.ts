import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  Post,
  Query,
} from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { ApiLogService } from './api-log.service';
import { CreateApiLogDto, QueryApiLogDto } from './dto/api-log.dto';
import { ApiLog } from 'src/common/decorators/api-log.decorator';
import { RequireAdmin } from 'src/common/decorators/require-admin.decorator';
import { RequireInternalToken } from 'src/common/decorators/require-internal-token.decorator';
import { ApiResponse, success } from 'src/common/utils/response';

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
  async findByFilter(
    @Query() query: QueryApiLogDto,
  ): Promise<ApiResponse<any>> {
    const data = await this.apiLogService.findByFilter(query);
    return success(data);
  }

  /**
   * 创建API日志
   */
  @Post()
  @ApiOperation({
    summary: '创建API日志',
    description: '创建一条API日志记录',
  })
  @ApiLog('创建API日志')
  @RequireAdmin()
  @RequireInternalToken()
  async create(@Body() dto: CreateApiLogDto): Promise<ApiResponse<any>> {
    await this.apiLogService.create(dto);
    return success(null);
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
  async remove(@Param('id') id: string): Promise<ApiResponse<any>> {
    await this.apiLogService.removeById(id);
    return success(null);
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
  async removeByIds(@Param('ids') ids: string): Promise<ApiResponse<any>> {
    const idArr = ids
      .split(',')
      .map((id) => id.trim())
      .filter(Boolean);
    await this.apiLogService.removeByIds(idArr);
    return success(null);
  }
}
