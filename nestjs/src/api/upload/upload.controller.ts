import { Body, Controller, Post, Req, Query } from '@nestjs/common';
import { ApiBody, ApiConsumes, ApiOperation, ApiTags, ApiQuery } from '@nestjs/swagger';
import type { FastifyRequest } from 'fastify';
import { ApiLog } from 'src/framework/decorators/api-log.decorator';
import { success } from 'src/common/utils/response';
import { UploadDto } from './dto/upload.dto';
import { UploadService } from './upload.service';
import { RequireInternalToken } from 'src/framework/decorators/require-internal-token.decorator';

@Controller('upload')
@ApiTags('文件上传')
export class UploadController {
  constructor(private readonly uploadService: UploadService) {}

  @Post('')
  @ApiOperation({ summary: '上传本地文件到 OSS', description: '通过本地文件路径上传文件到 OSS' })
  @RequireInternalToken()
  @ApiLog('上传文件到 OSS')
  async uploadFile(@Body() dto: UploadDto) {
    const url: string = await this.uploadService.uploadFile(
      dto.local_file,
      dto.oss_file,
    );
    return success(url);
  }

  @Post('image')
  @ApiConsumes('multipart/form-data')
  @ApiBody({
    schema: {
      type: 'object',
      properties: {
        file: {
          type: 'string',
          format: 'binary',
        },
      },
      required: ['file'],
    },
  })
  @ApiOperation({ summary: '上传图片到 OSS', description: '通过 multipart/form-data 上传图片到 OSS' })
  @ApiLog('上传图片到 OSS')
  async uploadImage(@Req() req: FastifyRequest) {
    const file = (req as any).body?.file;
    if (!file) {
      throw new Error('未找到文件部分');
    }
    const result = await this.uploadService.uploadImage(file);
    return success(result);
  }

  @Post('pdf')
  @ApiConsumes('multipart/form-data')
  @ApiBody({
    schema: {
      type: 'object',
      properties: {
        file: {
          type: 'string',
          format: 'binary',
        },
      },
      required: ['file'],
    },
  })
  @ApiQuery({
    name: 'custom_filename',
    type: 'string',
    required: false,
    description: '自定义文件名（不包含扩展名）',
  })
  @ApiOperation({ summary: '上传 PDF 到 OSS', description: '通过 multipart/form-data 上传 PDF 到 OSS' })
  @ApiLog('上传 PDF 到 OSS')
  async uploadPdf(
    @Req() req: FastifyRequest,
    @Query('custom_filename') customFilename?: string,
  ) {
    const file = (req as any).body?.file;
    if (!file) {
      throw new Error('未找到文件部分');
    }
    const result = await this.uploadService.uploadPdf(file, customFilename);
    return success(result);
  }
}
