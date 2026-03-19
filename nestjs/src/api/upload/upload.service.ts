import { Injectable, BadRequestException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { pipeline, Readable } from 'stream';
import { promisify } from 'util';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as crypto from 'crypto';
import { OssService } from 'src/modules/oss/oss.service';
import { logger } from 'src/common/utils/writeLog';
import { UploadResult } from './dto/upload.dto';

const pump = promisify(pipeline);

@Injectable()
export class UploadService {
  constructor(
    private readonly ossService: OssService,
    private readonly configService: ConfigService,
  ) {}

  /**
   * 上传本地文件到 OSS
   */
  async uploadFile(localFile: string, ossFile: string): Promise<string> {
    return this.ossService.uploadFile(localFile, ossFile);
  }

  /**
   * 上传图片到 OSS
   */
  async uploadImage(file: any): Promise<UploadResult> {
    const originalFilename = file.filename || 'image';
    const fileExtension = path.extname(originalFilename).toLowerCase() || '.jpg';
    const uniqueFilename = `${crypto.randomUUID()}${fileExtension}`;

    // 保存到本地临时目录
    const localPath = await this.saveFileToTemp(file, uniqueFilename, [
      '.png',
      '.jpg',
      '.jpeg',
      '.gif',
      '.webp',
    ]);

    try {
      // 上传到 OSS
      const ossPath = `pic/${uniqueFilename}`;
      const ossUrl = await this.ossService.uploadFile(localPath, ossPath);

      return {
        original_filename: originalFilename,
        oss_filename: uniqueFilename,
        oss_url: ossUrl,
      };
    } finally {
      // 删除本地临时文件
      await this.cleanupTempFile(localPath);
    }
  }

  /**
   * 上传 PDF 到 OSS（参照 FastAPI 逻辑）
   */
  async uploadPdf(file: any, customFilename?: string): Promise<UploadResult> {
    const originalFilename = file.filename || 'document.pdf';
    const fileExtension = path.extname(originalFilename).toLowerCase();

    if (fileExtension !== '.pdf') {
      throw new BadRequestException('只支持上传 PDF 文件');
    }

    // 如果提供了自定义文件名，使用自定义文件名；否则生成 UUID
    let uniqueFilename: string;
    if (customFilename) {
      uniqueFilename = `${customFilename}.pdf`;
    } else {
      uniqueFilename = `${crypto.randomUUID()}${fileExtension}`;
    }

    // 保存到本地临时目录
    const localPath = await this.saveFileToTemp(file, uniqueFilename);

    try {
      // 上传到 OSS
      const ossPath = `pdf/${uniqueFilename}`;
      const ossUrl = await this.ossService.uploadFile(localPath, ossPath);

      return {
        original_filename: originalFilename,
        oss_filename: uniqueFilename,
        oss_url: ossUrl,
      };
    } finally {
      // 删除本地临时文件
      await this.cleanupTempFile(localPath);
    }
  }

  private async saveFileToTemp(
    file: any,
    filename: string,
    allowExt?: string[],
  ): Promise<string> {
    // fastify-multipart 返回的文件对象本身就是 Readable 流
    if (!file) {
      throw new BadRequestException('未上传文件');
    }

    const originalFilename = file.filename || '';
    if (allowExt && allowExt.length > 0) {
      const ext = path.extname(originalFilename).toLowerCase() || '';
      if (!allowExt.includes(ext)) {
        logger.error(`不支持的文件格式: ${ext}，允许格式: ${allowExt.join(', ')}`);
        throw new BadRequestException(
          `仅支持以下格式: ${allowExt.join(', ')}`,
        );
      }
    }

    // 从配置中获取上传目录，如果没有配置则使用系统临时目录
    let uploadDir: string = this.configService.get<string>(
      'files.upload',
    ) || path.join(os.tmpdir(), 'nestjs-upload');
    
    // 如果是相对路径，转换为绝对路径
    if (!path.isAbsolute(uploadDir)) {
      uploadDir = path.join(process.cwd(), uploadDir);
    }
    
    await fs.promises.mkdir(uploadDir, { recursive: true });
    const localPath = path.join(uploadDir, filename);

    try {
      // 文件对象本身是一个流，直接使用
      await pump(file as Readable, fs.createWriteStream(localPath));
      logger.info(`文件已保存到临时目录: ${localPath}`);
      return localPath;
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      logger.error(`保存文件到临时目录失败: ${message}`);
      throw error;
    }
  }

  private async cleanupTempFile(filePath: string): Promise<void> {
    try {
      await fs.promises.unlink(filePath);
      logger.info(`临时文件已删除: ${filePath}`);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      logger.warning(`删除临时文件失败: ${message}`);
    }
  }
}
