import {
  Body,
  Controller,
  Delete,
  Get,
  HttpCode,
  Param,
  Post,
  Query,
} from '@nestjs/common';
import { ArticleLogService } from './article-log.service';
import { CreateArticleLogDto, QueryArticleLogDto } from './dto/article-log.dto';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { ApiLog } from 'src/common/decorators/api-log.decorator';
import { RequireAdmin } from 'src/common/decorators/require-admin.decorator';
import { success } from 'src/common/utils/response';

@Controller('article-logs')
@ApiTags('文章日志模块')
export class ArticleLogController {
  constructor(private readonly logService: ArticleLogService) {}

  @Post()
  @HttpCode(200)
  @ApiOperation({
    summary: '新增文章日志',
    description: '通过请求体创建文章日志',
  })
  @ApiLog('新增文章日志')
  @RequireAdmin()
  async create(@Body() dto: CreateArticleLogDto) {
    await this.logService.create(dto);
    return success(null);
  }

  @Get('list')
  @ApiOperation({
    summary: '查询文章日志',
    description: '可根据用户ID、文章ID、操作类型查询，支持分页',
  })
  @ApiLog('查询文章日志')
  @RequireAdmin()
  async findByFilter(@Query() query: QueryArticleLogDto): Promise<any> {
    const data: any = await this.logService.findByFilter(query);
    return success(data);
  }
  @Delete(':id')
  @ApiOperation({
    summary: '删除文章日志',
    description: '通过文章日志 ID 删除日志',
  })
  @ApiLog('删除文章日志')
  @RequireAdmin()
  async remove(@Param('id') id: string): Promise<any> {
    await this.logService.removeById(id);
    return success(null);
  }

  @Delete('batch/:ids')
  @ApiOperation({
    summary: '批量删除文章日志',
    description: '通过日志ID路径参数批量删除，多个ID用英文逗号分隔',
  })
  @ApiLog('批量删除文章日志')
  @RequireAdmin()
  async removeByIds(@Param('ids') ids: string): Promise<any> {
    const idArr: string[] = ids
      .split(',')
      .map((id: string) => id.trim())
      .filter(Boolean);
    await this.logService.removeByIds(idArr);
    return success(null);
  }
}
