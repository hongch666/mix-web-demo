import { Controller, Get, Param, Logger } from '@nestjs/common';
import { ArticleService } from './article.service';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { ClsService } from 'nestjs-cls';

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
    Logger.log(
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
}
