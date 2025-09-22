import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  Post,
  Query,
} from '@nestjs/common';
import { ArticleLogService } from './log.service';
import { CreateArticleLogDto, QueryArticleLogDto } from './dto';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { ApiLog } from 'src/common/decorators/api-log.decorator';

@Controller('logs')
@ApiTags('日志模块')
export class ArticleLogController {
  constructor(private readonly logService: ArticleLogService) {}

  @Post()
  @ApiOperation({ summary: '新增日志', description: '通过请求体创建日志' })
  @ApiLog('新增日志')
  async create(@Body() dto: CreateArticleLogDto) {
    await this.logService.create(dto);
    return null;
  }

  @Get('list')
  @ApiOperation({
    summary: '查询日志',
    description: '可根据用户ID、文章ID、操作类型查询，支持分页',
  })
  @ApiLog('查询日志')
  async findByFilter(@Query() query: QueryArticleLogDto) {
    return await this.logService.findByFilter(query);
  }

  @Delete(':id')
  @ApiOperation({ summary: '删除日志', description: '通过日志 ID 删除日志' })
  @ApiLog('删除日志')
  async remove(@Param('id') id: string) {
    await this.logService.removeById(id);
    return null;
  }

  @Delete('batch/:ids')
  @ApiOperation({
    summary: '批量删除日志',
    description: '通过日志ID路径参数批量删除，多个ID用英文逗号分隔',
  })
  @ApiLog('批量删除日志')
  async removeByIds(@Param('ids') ids: string) {
    const idArr = ids
      .split(',')
      .map((id) => id.trim())
      .filter(Boolean);
    await this.logService.removeByIds(idArr);
    return null;
  }
}
