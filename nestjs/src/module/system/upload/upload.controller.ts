import { Body, Controller, Post, Query, Req } from '@nestjs/common';
import {
  ApiBody,
  ApiConsumes,
  ApiOperation,
  ApiQuery,
  ApiTags,
} from '@nestjs/swagger';
import type { FastifyRequest } from 'fastify';
import { BusinessException } from 'src/common/exceptions/business.exception';
import { Constants } from 'src/common/utils/constants';
import { ApiResponse, success } from 'src/common/utils/response';
import { ApiLog } from 'src/framework/decorators/apiLog.decorator';
import { RequireInternalToken } from 'src/framework/decorators/requireInternalToken.decorator';
import { UploadDto, UploadResult } from './dto/upload.dto';
import { MultipartUploadFile, UploadService } from './upload.service';

@Controller('upload')
@ApiTags('文件上传')
export class UploadController {
  constructor(private readonly uploadService: UploadService) {}

  @Post('')
  @ApiOperation({
    summary: '上传本地文件到 OSS',
    description: '通过本地文件路径上传文件到 OSS',
  })
  @RequireInternalToken()
  @ApiLog('上传文件到 OSS')
  async uploadFile(@Body() dto: UploadDto): Promise<ApiResponse<string>> {
    const url: string = await this.uploadService.uploadFile(
      dto.localFile,
      dto.ossFile,
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
  @ApiOperation({
    summary: '上传图片到 OSS',
    description: '通过 multipart/form-data 上传图片到 OSS',
  })
  @ApiLog('上传图片到 OSS')
  async uploadImage(
    @Req() req: FastifyRequest,
  ): Promise<ApiResponse<UploadResult>> {
    const parts = req.parts();
    for await (const part of parts) {
      if ('filename' in part && part.filename) {
        const result: UploadResult = await this.uploadService.uploadImage(
          part as MultipartUploadFile,
        );
        return success(result);
      }
    }
    throw BusinessException.notFound(Constants.FILE_PART_NOT_FOUND);
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
  @ApiOperation({
    summary: '上传 PDF 到 OSS',
    description: '通过 multipart/form-data 上传 PDF 到 OSS',
  })
  @ApiLog('上传 PDF 到 OSS')
  async uploadPdf(
    @Req() req: FastifyRequest,
    @Query('customFilename') customFilename?: string,
  ): Promise<ApiResponse<UploadResult>> {
    const parts = req.parts();
    for await (const part of parts) {
      if ('filename' in part && part.filename) {
        const result: UploadResult = await this.uploadService.uploadPdf(
          part as MultipartUploadFile,
          customFilename,
        );
        return success(result);
      }
    }
    throw BusinessException.notFound(Constants.FILE_PART_NOT_FOUND);
  }
}
