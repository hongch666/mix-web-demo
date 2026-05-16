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
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { ApiResponse, success } from 'src/common/utils/response';
import { ApiLog } from 'src/framework/decorators/apiLog.decorator';
import { RequireAdmin } from 'src/framework/decorators/requireAdmin.decorator';
import { RequireInternalToken } from 'src/framework/decorators/requireInternalToken.decorator';
import { ArticleLogService } from './articleLog.service';
import { CreateArticleLogDto, QueryArticleLogDto } from './dto/articleLog.dto';

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
  @RequireInternalToken()
  async create(@Body() dto: CreateArticleLogDto): Promise<ApiResponse<null>> {
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
  async findByFilter(
    @Query() query: QueryArticleLogDto,
  ): Promise<ApiResponse<unknown>> {
    const data: unknown = await this.logService.findByFilter(query);
    return success(data);
  }

  @Get('search-history/:userId')
  @ApiOperation({
    summary: '查询用户搜索历史',
    description: '供 GoZero 搜索模块获取用户搜索历史',
  })
  @RequireInternalToken()
  async getSearchHistory(
    @Param('userId') userId: string,
  ): Promise<ApiResponse<unknown>> {
    const data = await this.logService.getSearchHistory(Number(userId));
    return success(data);
  }

  @Get('search-keywords')
  @ApiOperation({
    summary: '查询搜索关键词',
    description: '供 FastAPI 词云分析使用',
  })
  @RequireInternalToken()
  async getSearchKeywords(): Promise<ApiResponse<unknown>> {
    const data = await this.logService.getSearchKeywords();
    return success(data);
  }

  @Get('view-distribution')
  @ApiOperation({
    summary: '查询用户浏览分布',
    description: '供 FastAPI 用户分析使用',
  })
  @RequireInternalToken()
  async getViewDistribution(
    @Query('userId') userId: string,
  ): Promise<ApiResponse<unknown>> {
    const data = await this.logService.getViewDistribution(Number(userId));
    return success(data);
  }

  @Delete(':id')
  @ApiOperation({
    summary: '删除文章日志',
    description: '通过文章日志 ID 删除日志',
  })
  @ApiLog('删除文章日志')
  @RequireAdmin()
  async remove(@Param('id') id: string): Promise<ApiResponse<null>> {
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
  async removeByIds(@Param('ids') ids: string): Promise<ApiResponse<null>> {
    const idArr: string[] = ids
      .split(',')
      .map((id: string) => id.trim())
      .filter(Boolean);
    await this.logService.removeByIds(idArr);
    return success(null);
  }
}
