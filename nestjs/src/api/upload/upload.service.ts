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
    logger.info(`uploadImage 开始，文件信息: filename=${file?.filename}`);
    logger.info(`文件对象类型: ${typeof file}, 是否有 readable: ${file?.readable}, 是否有 pipe: ${typeof file?.pipe}`);
    logger.info(`文件对象键: ${Object.keys(file || {}).join(', ')}`);
    
    const originalFilename = file.filename || 'image';
    const fileExtension = path.extname(originalFilename).toLowerCase() || '.jpg';
    const uniqueFilename = `${crypto.randomUUID()}${fileExtension}`;
    logger.info(`生成唯一文件名: ${uniqueFilename}`);

    // 保存到本地临时目录
    logger.info(`开始保存文件到临时目录...`);
    const localPath = await this.saveFileToTemp(file, uniqueFilename, [
      '.png',
      '.jpg',
      '.jpeg',
      '.gif',
      '.webp',
    ]);
    logger.info(`文件已保存到临时目录: ${localPath}`);

    try {
      // 上传到 OSS
      logger.info(`开始上传文件到 OSS...`);
      const ossPath = `pic/${uniqueFilename}`;
      logger.info(`OSS 目标路径: ${ossPath}`);
      
      const ossUrl = await this.ossService.uploadFile(localPath, ossPath);
      logger.info(`OSS 上传完成，URL: ${ossUrl}`);

      return {
        original_filename: originalFilename,
        oss_filename: uniqueFilename,
        oss_url: ossUrl,
      };
    } finally {
      // 删除本地临时文件
      logger.info(`开始清理临时文件...`);
      await this.cleanupTempFile(localPath);
      logger.info(`临时文件清理完成`);
    }
  }

  /**
   * 上传 PDF 到 OSS（参照 FastAPI 逻辑）
   */
  async uploadPdf(file: any, customFilename?: string): Promise<UploadResult> {
    logger.info(`uploadPdf 开始，文件信息: filename=${file?.filename}`);
    
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
    logger.info(`生成唯一文件名: ${uniqueFilename}`);

    // 保存到本地临时目录
    logger.info(`开始保存文件到临时目录...`);
    const localPath = await this.saveFileToTemp(file, uniqueFilename);
    logger.info(`文件已保存到临时目录: ${localPath}`);

    try {
      // 上传到 OSS
      logger.info(`开始上传文件到 OSS...`);
      const ossPath = `pdf/${uniqueFilename}`;
      logger.info(`OSS 目标路径: ${ossPath}`);
      
      const ossUrl = await this.ossService.uploadFile(localPath, ossPath);
      logger.info(`OSS 上传完成，URL: ${ossUrl}`);

      return {
        original_filename: originalFilename,
        oss_filename: uniqueFilename,
        oss_url: ossUrl,
      };
    } finally {
      // 删除本地临时文件
      logger.info(`开始清理临时文件...`);
      await this.cleanupTempFile(localPath);
      logger.info(`临时文件清理完成`);
    }
  }

  private async saveFileToTemp(
    file: any,
    filename: string,
    allowExt?: string[],
  ): Promise<string> {
    // 禁用 attachFieldsToBody 后，file 本身就是流对象，有 filename、encoding、mimetype 等属性
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
      // 文件对象本身是一个流
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
