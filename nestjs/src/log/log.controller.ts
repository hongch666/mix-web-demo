import { Body, Controller, Get, Param, Post } from '@nestjs/common';
import { ArticleLogService } from './log.service';
import { CreateArticleLogDto } from './dto';
import { ApiOperation, ApiTags } from '@nestjs/swagger';

@Controller('logs')
@ApiTags('日志模块')
export class ArticleLogController {
  constructor(private readonly logService: ArticleLogService) {}

  @Post()
  @ApiOperation({ summary: '新增日志', description: '通过请求体创建日志' })
  create(@Body() dto: CreateArticleLogDto) {
    this.logService.create(dto);
    return null;
  }

  @Get()
  @ApiOperation({
    summary: '查询所有日志',
    description: '获取全部日志记录',
  })
  findAll() {
    return this.logService.findAll();
  }

  @Get('article/:articleId')
  @ApiOperation({
    summary: '根据文章id查询日志',
    description: '根据文章id查询日志',
  })
  findByArticle(@Param('articleId') articleId: string) {
    return this.logService.findAllByArticle(articleId);
  }

  @Get('user/:userId')
  @ApiOperation({
    summary: '根据用户id查询日志',
    description: '根据用户id查询日志',
  })
  findByUser(@Param('userId') userId: string) {
    return this.logService.findAllByUser(userId);
  }
}
