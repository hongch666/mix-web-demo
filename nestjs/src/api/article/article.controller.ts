import { Controller, Get, Param } from '@nestjs/common';
import { ArticleService } from './article.service';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { ClsService } from 'nestjs-cls';
import { fileLogger } from 'src/common/utils/writeLog';

@Controller('article')
@ApiTags('文章模块')
export class ArticleController {
  constructor(
    private readonly articleService: ArticleService,
    private readonly cls: ClsService,
  ) {}

  @Get('download/:id')
  @ApiOperation({ summary: '下载文章', description: '通过id下载对应文章' })
  async downloadWord(@Param('id') id: number) {
    const userId = this.cls.get('userId');
    const username = this.cls.get('username');
    fileLogger.info(
      '用户' +
        userId +
        ':' +
        username +
        ' GET /article/download/:id' +
        '下载文章\n' +
        'ID: ' +
        id,
    );
    const url = await this.articleService.exportToWordAndSave(id);
    return url;
  }

  @Get('download-markdown/:id')
  @ApiOperation({
    summary: '下载文章Markdown',
    description: '通过id下载对应文章的Markdown并返回OSS链接',
  })
  async downloadMarkdown(@Param('id') id) {
    const userId = this.cls.get('userId');
    const username = this.cls.get('username');
    fileLogger.info(
      '用户' +
        userId +
        ':' +
        username +
        ' GET /article/download-markdown/:id' +
        '下载文章Markdown\n' +
        'ID: ' +
        id,
    );
    const url = await this.articleService.exportMarkdownAndUpload(Number(id));
    return url;
  }
}
