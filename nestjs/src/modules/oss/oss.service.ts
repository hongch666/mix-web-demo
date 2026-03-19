import { Injectable, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { logger } from 'src/common/utils/writeLog';
import { BusinessException } from 'src/common/exceptions/business.exception';

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
      (config['access_key_id'] as string) ||
      (config['accessKeyId'] as string);
    const accessKeySecret: string | undefined =
      (config['access_key_secret'] as string) ||
      (config['accessKeySecret'] as string);
    this.bucketName = (config['bucket_name'] as string) ||
      (config['bucketName'] as string);
    this.endpoint = (config['endpoint'] as string) || '';

    if (!accessKeyId || !accessKeySecret || !this.bucketName || !this.endpoint) {
      throw new BusinessException(
        'OSS 配置不完整，请检查 application.yaml 中的 oss 配置',
      );
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
      logger.info(`开始上传文件到 OSS: localFile=${localFile}, ossFile=${ossFile}`);
      logger.info(`OSS 客户端配置: bucket=${this.bucketName}, endpoint=${this.endpoint}`);
      
      const result = await this.client.put(ossFile, localFile);
      logger.info(`OSS put 返回结果: ${JSON.stringify(result)}`);
      
      const url: string = this.getFileUrl(ossFile);
      logger.info(`OSS 文件上传成功: ${url}`);
      return url;
    } catch (error: unknown) {
      const message: string =
        error instanceof Error ? error.message : String(error);
      logger.error(`OSS 上传失败: ${message}`);
      logger.error(`失败的 localFile: ${localFile}, ossFile: ${ossFile}`);
      throw new BusinessException('OSS 上传失败');
    }
  }

  /**
   * 获取 OSS 文件访问 URL（假设 bucket 为公开读）
   */
  getFileUrl(ossFile: string): string {
    return `https://${this.bucketName}.${this.endpoint}/${ossFile}`;
  }
}
