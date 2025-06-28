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
import { ClsService } from 'nestjs-cls';
import { fileLogger } from 'src/common/utils/writeLog';

@Controller('logs')
@ApiTags('日志模块')
export class ArticleLogController {
  constructor(
    private readonly logService: ArticleLogService,
    private readonly cls: ClsService,
  ) {}

  @Post()
  @ApiOperation({ summary: '新增日志', description: '通过请求体创建日志' })
  async create(@Body() dto: CreateArticleLogDto) {
    const userId = this.cls.get('userId');
    const username = this.cls.get('username');
    fileLogger.info(
      '用户' +
        userId +
        ':' +
        username +
        ' POST /logs: ' +
        '新增日志\nCreateArticleLogDto: ' +
        JSON.stringify(dto),
    );
    await this.logService.create(dto);
    return null;
  }

  @Get('list')
  @ApiOperation({
    summary: '查询日志',
    description: '可根据用户ID、文章ID、操作类型查询，支持分页',
  })
  async findByFilter(@Query() query: QueryArticleLogDto) {
    const userId = this.cls.get('userId');
    const username = this.cls.get('username');
    fileLogger.info(
      '用户' +
        userId +
        ':' +
        username +
        ' GET /logs/list: ' +
        '查询日志\nQueryArticleLogDto: ' +
        JSON.stringify(query),
    );
    return await this.logService.findByFilter(query);
  }

  @Delete(':id')
  @ApiOperation({ summary: '删除日志', description: '通过日志 ID 删除日志' })
  async remove(@Param('id') id: string) {
    const userId = this.cls.get('userId');
    const username = this.cls.get('username');
    fileLogger.info(
      '用户' +
        userId +
        ':' +
        username +
        ' DELETE /logs/:id: ' +
        '删除日志\nID: ' +
        id,
    );
    await this.logService.removeById(id);
    return null;
  }
}
