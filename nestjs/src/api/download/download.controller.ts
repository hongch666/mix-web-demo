import { Controller, Get, Param } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { ApiLog } from 'src/common/decorators/api-log.decorator';
import { ArticleService } from 'src/modules/article/article.service';

@Controller('download')
@ApiTags('下载模块')
export class DownloadController {
  constructor(private readonly articleService: ArticleService) {}

  @Get('word/:id')
  @ApiOperation({ summary: '下载文章', description: '通过id下载对应文章' })
  @ApiLog('下载文章')
  async downloadWord(@Param('id') id: number) {
    const url = await this.articleService.exportToWordAndSave(id);
    return url;
  }

  @Get('markdown/:id')
  @ApiOperation({
    summary: '下载文章Markdown',
    description: '通过id下载对应文章的Markdown并返回OSS链接',
  })
  @ApiLog('下载文章Markdown')
  async downloadMarkdown(@Param('id') id) {
    const url = await this.articleService.exportMarkdownAndUpload(Number(id));
    return url;
  }

  @Get('pdf/:id')
  @ApiOperation({
    summary: '下载文章PDF',
    description: '通过id下载对应文章的PDF并返回OSS链接',
  })
  @ApiLog('下载文章PDF')
  async downloadPdf(@Param('id') id: number) {
    const url = await this.articleService.exportToPdfAndSave(id);
    return url;
  }
}
