import { Body, Controller, Get, Param, Post } from '@nestjs/common';
import { ArticleLogService } from './log.service';
import { CreateArticleLogDto } from './dto';

@Controller('article-logs')
export class ArticleLogController {
  constructor(private readonly logService: ArticleLogService) {}

  @Post()
  create(@Body() dto: CreateArticleLogDto) {
    return this.logService.create(dto);
  }

  @Get('article/:articleId')
  findByArticle(@Param('articleId') articleId: string) {
    return this.logService.findAllByArticle(articleId);
  }

  @Get('user/:userId')
  findByUser(@Param('userId') userId: string) {
    return this.logService.findAllByUser(userId);
  }
}
