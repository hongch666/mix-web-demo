import { Controller, Get, Param } from '@nestjs/common';
import { ArticleService } from './article.service';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { ApiLog } from 'src/common/decorators/api-log.decorator';

@Controller('article')
@ApiTags('文章模块')
export class ArticleController {
  constructor(private readonly articleService: ArticleService) {}

  @Get('download/:id')
  @ApiOperation({ summary: '下载文章', description: '通过id下载对应文章' })
  @ApiLog('下载文章')
  async downloadWord(@Param('id') id: number) {
    const url = await this.articleService.exportToWordAndSave(id);
    return url;
  }

  @Get('download-markdown/:id')
  @ApiOperation({
    summary: '下载文章Markdown',
    description: '通过id下载对应文章的Markdown并返回OSS链接',
  })
  @ApiLog('下载文章Markdown')
  async downloadMarkdown(@Param('id') id) {
    const url = await this.articleService.exportMarkdownAndUpload(Number(id));
    return url;
  }
}
