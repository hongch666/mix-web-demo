import {
  Controller,
  Get,
  Param,
  HttpException,
  HttpStatus,
} from '@nestjs/common';
import { ApiOperation, ApiTags, ApiParam } from '@nestjs/swagger';
import { ApiLog } from 'src/common/decorators/api-log.decorator';
import { DownloadService } from './download.service';

@Controller('download')
@ApiTags('下载模块')
export class DownloadController {
  constructor(private readonly downloadService: DownloadService) {}

  @Get('word/:id')
  @ApiOperation({
    summary: '下载文章Word',
    description: '通过id下载对应文章Word',
  })
  @ApiParam({ name: 'id', type: 'number', description: '文章ID' })
  @ApiLog('下载文章Word')
  async downloadWord(@Param('id') id: number) {
    try {
      const url = await this.downloadService.exportToWordAndSave(id);
      return url;
    } catch (error) {
      throw new HttpException(
        error.message || '下载文章Word失败',
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }

  @Get('markdown/:id')
  @ApiOperation({
    summary: '下载文章Markdown',
    description: '通过id下载对应文章的Markdown并返回OSS链接',
  })
  @ApiParam({ name: 'id', type: 'number', description: '文章ID' })
  @ApiLog('下载文章Markdown')
  async downloadMarkdown(@Param('id') id) {
    try {
      const url = await this.downloadService.exportMarkdownAndUpload(
        Number(id),
      );
      return url;
    } catch (error) {
      throw new HttpException(
        error.message || '下载文章Markdown失败',
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }

  @Get('pdf/:id')
  @ApiOperation({
    summary: '下载文章PDF',
    description: '通过id下载对应文章的PDF并返回OSS链接',
  })
  @ApiParam({ name: 'id', type: 'number', description: '文章ID' })
  @ApiLog('下载文章PDF')
  async downloadPdf(@Param('id') id: number) {
    try {
      const url = await this.downloadService.exportToPdfAndSave(id);
      return url;
    } catch (error) {
      throw new HttpException(
        error.message || '下载文章PDF失败',
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }
}
