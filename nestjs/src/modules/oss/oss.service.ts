import { Injectable, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as crypto from 'crypto';
import * as fs from 'fs';
import { BusinessException } from 'src/common/exceptions/business.exception';
import { Constants } from 'src/common/utils/constants';
import { logger } from 'src/common/utils/writeLog';

import type OSS from 'ali-oss';

export interface OssConfig {
  access_key_id: string;
  access_key_secret: string;
  bucket_name: string;
  endpoint: string;
}

@Injectable()
export class OssService implements OnModuleInit {
  private client: OSS | null = null;
  private bucketName!: string;
  private endpoint!: string;
  private accessKeyId!: string;
  private accessKeySecret!: string;

  constructor(private readonly configService: ConfigService) {}

  async onModuleInit(): Promise<void> {
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

    this.accessKeyId = accessKeyId;
    this.accessKeySecret = accessKeySecret;

    if (this.isBunRuntime()) {
      logger.info(Constants.OSS_BUN_RUNTIME_COMPAT_MESSAGE);
      return;
    }

    const { default: OSS } = await import('ali-oss');
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
      const result = this.isBunRuntime()
        ? await this.uploadFileWithBun(localFile, ossFile)
        : await this.uploadFileWithAliOss(localFile, ossFile);

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

  private isBunRuntime(): boolean {
    return Boolean(
      (process as NodeJS.Process & { versions?: { bun?: string } }).versions
        ?.bun,
    );
  }

  private async uploadFileWithAliOss(
    localFile: string,
    ossFile: string,
  ): Promise<unknown> {
    if (!this.client) {
      throw new Error(Constants.OSS_CLIENT_NOT_INITIALIZED);
    }

    const uploadPromise = this.client.put(ossFile, localFile);
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(
        () => reject(new Error(Constants.OSS_PUT_OPERATION_TIMEOUT)),
        30000,
      ),
    );

    return Promise.race([uploadPromise, timeoutPromise]);
  }

  private async uploadFileWithBun(
    localFile: string,
    ossFile: string,
  ): Promise<unknown> {
    const fileBuffer = await fs.promises.readFile(localFile);
    const normalizedOssFile: string = ossFile.replace(/^\/+/, '');
    const requestPath: string = `/${this.bucketName}/${normalizedOssFile}`;
    const requestUrl: string = `https://${this.bucketName}.${this.endpoint}/${this.encodeOssPath(normalizedOssFile)}`;
    const contentType: string = Constants.OSS_DEFAULT_CONTENT_TYPE;
    const requestDate: string = new Date().toUTCString();
    const stringToSign: string = [
      Constants.OSS_HTTP_PUT_METHOD,
      '',
      contentType,
      requestDate,
      requestPath,
    ].join('\n');
    const signature: string = crypto
      .createHmac('sha1', this.accessKeySecret)
      .update(stringToSign)
      .digest('base64');
    const timeoutController = new AbortController();
    const timeoutId = setTimeout(() => timeoutController.abort(), 30000);

    try {
      const response: Response = await fetch(requestUrl, {
        method: 'PUT',
        headers: {
          Authorization: `OSS ${this.accessKeyId}:${signature}`,
          Date: requestDate,
          'Content-Type': contentType,
          'Content-Length': String(fileBuffer.byteLength),
        },
        body: new Uint8Array(fileBuffer),
        signal: timeoutController.signal,
      });

      if (!response.ok) {
        const responseText: string = await response.text();
        throw new Error(
          `${Constants.OSS_RESPONSE_NON_SUCCESS_PREFIX}: ${response.status} ${response.statusText}，${Constants.OSS_RESPONSE_CONTENT_PREFIX} ${responseText}`,
        );
      }

      return {
        name: normalizedOssFile,
        url: this.getFileUrl(normalizedOssFile),
        res: {
          status: response.status,
          statusText: response.statusText,
        },
      };
    } catch (error: unknown) {
      if (timeoutController.signal.aborted) {
        throw new Error(Constants.OSS_PUT_OPERATION_TIMEOUT);
      }

      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  private encodeOssPath(ossFile: string): string {
    return ossFile
      .split('/')
      .map((segment: string) => encodeURIComponent(segment))
      .join('/');
  }
}
