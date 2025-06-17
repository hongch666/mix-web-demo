import { Controller, Get, Param, Logger } from '@nestjs/common';
import { ArticleService } from './article.service';
import { ApiOperation, ApiTags } from '@nestjs/swagger';

@Controller('article')
@ApiTags('文章模块')
export class ArticleController {
  constructor(private readonly articleService: ArticleService) {}

  @Get('download/:id')
  @ApiOperation({ summary: '下载文章', description: '通过id下载对应文章' })
  async downloadWord(@Param('id') id: number) {
    Logger.log('GET /article/download/:id' + '下载文章\n' + 'ID: ' + id);
    const url = await this.articleService.exportToWordAndSave(id);
    return url;
  }
}
