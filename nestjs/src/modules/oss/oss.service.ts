import { Injectable, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { logger } from 'src/common/utils/writeLog';
import { BusinessException } from 'src/common/exceptions/business.exception';
import { Constants } from 'src/common/utils/constants';
import * as fs from 'fs';

import OSS from 'ali-oss';

export interface OssConfig {
  access_key_id: string;
  access_key_secret: string;
  bucket_name: string;
  endpoint: string;
}

@Injectable()
export class OssService implements OnModuleInit {
  private client!: OSS;
  private bucketName!: string;
  private endpoint!: string;

  constructor(private readonly configService: ConfigService) {}

  onModuleInit(): void {
    const config: Record<string, unknown> =
      this.configService.get<Record<string, unknown>>('oss') ?? {};

    const accessKeyId: string | undefined =
      (config['access_key_id'] as string) || (config['accessKeyId'] as string);
    const accessKeySecret: string | undefined =
      (config['access_key_secret'] as string) ||
      (config['accessKeySecret'] as string);
    this.bucketName =
      (config['bucket_name'] as string) || (config['bucketName'] as string);
    this.endpoint = (config['endpoint'] as string) || '';

    if (
      !accessKeyId ||
      !accessKeySecret ||
      !this.bucketName ||
      !this.endpoint
    ) {
      throw new BusinessException(Constants.OSS_CONFIG_INCOMPLETE);
    }

    this.client = new OSS({
      accessKeyId,
      accessKeySecret,
      bucket: this.bucketName,
      endpoint: this.endpoint,
      secure: true,
    });
  }

  /**
   * 上传本地文件到 OSS
   * @param localFile 本地绝对路径
   * @param ossFile OSS 目标路径（例如："articles/xxx.docx"）
   */
  async uploadFile(localFile: string, ossFile: string): Promise<string> {
    try {
      logger.info(
        `开始上传文件到 OSS: localFile=${localFile}, ossFile=${ossFile}`,
      );
      logger.info(
        `OSS 客户端配置: bucket=${this.bucketName}, endpoint=${this.endpoint}`,
      );

      // 检查文件是否存在
      logger.info(`检查本地文件是否存在: ${localFile}`);
      const fileExists = fs.existsSync(localFile);
      logger.info(`文件存在性检查结果: ${fileExists}`);

      if (!fileExists) {
        throw new Error(`本地文件不存在: ${localFile}`);
      }

      // 获取文件大小
      const stats = fs.statSync(localFile);
      logger.info(`本地文件大小: ${stats.size} bytes`);

      // 添加超时控制（30秒）
      logger.info(Constants.OSS_PUT_OPERATION_START);
      const uploadPromise = this.client.put(ossFile, localFile);
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('OSS put 操作超时（30秒）')), 30000),
      );

      const result = await Promise.race([uploadPromise, timeoutPromise]);
      logger.info(`OSS put 返回结果: ${JSON.stringify(result)}`);

      const url: string = this.getFileUrl(ossFile);
      logger.info(`OSS 文件上传成功: ${url}`);
      return url;
    } catch (error: unknown) {
      const message: string =
        error instanceof Error ? error.message : String(error);
      logger.error(`OSS 上传失败: ${message}`);
      logger.error(`失败的 localFile: ${localFile}, ossFile: ${ossFile}`);
      logger.error(`错误堆栈: ${error instanceof Error ? error.stack : ''}`);
      throw new BusinessException(Constants.OSS_UPLOAD_FAILED);
    }
  }

  /**
   * 获取 OSS 文件访问 URL（假设 bucket 为公开读）
   */
  getFileUrl(ossFile: string): string {
    return `https://${this.bucketName}.${this.endpoint}/${ossFile}`;
  }
}
