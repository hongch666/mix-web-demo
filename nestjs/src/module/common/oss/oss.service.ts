import { Injectable, OnModuleInit } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import * as crypto from "crypto";
import * as fs from "fs";
import { Defaults, Messages } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { logger } from "src/common/utils/writeLog";

import type OSS from "ali-oss";

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
  private putTimeout: number = 120000; // 默认 120 秒，通过 config 覆盖

  constructor(private readonly configService: ConfigService) {}

  async onModuleInit(): Promise<void> {
    const config: Record<string, unknown> =
      this.configService.get<Record<string, unknown>>("oss") ?? {};

    const accessKeyId: string | undefined =
      (config["access_key_id"] as string) || (config["accessKeyId"] as string);
    const accessKeySecret: string | undefined =
      (config["access_key_secret"] as string) ||
      (config["accessKeySecret"] as string);
    this.bucketName =
      (config["bucket_name"] as string) || (config["bucketName"] as string);
    this.endpoint = (config["endpoint"] as string) || "";

    if (
      !accessKeyId ||
      !accessKeySecret ||
      !this.bucketName ||
      !this.endpoint
    ) {
      throw BusinessException.serviceUnavailable(
        Messages.OSS_CONFIG_INCOMPLETE,
      );
    }

    this.accessKeyId = accessKeyId;
    this.accessKeySecret = accessKeySecret;

    // 读取上传超时配置（秒转换为毫秒）
    const putTimeoutSec: number = Number(
      (config["put_timeout"] as string) ||
        (config["putTimeout"] as string) ||
        "120",
    );
    this.putTimeout = Math.max(putTimeoutSec, 10) * 1000; // 最少 10 秒

    if (this.isBunRuntime()) {
      logger.info(Messages.OSS_BUN_RUNTIME_COMPAT_MESSAGE);
      return;
    }

    const { default: OSS } = await import("ali-oss");
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
        Messages.OSS_UPLOAD_START_DETAIL(localFile, ossFile),
      );
      logger.info(
        Messages.OSS_CLIENT_CONFIG_INFO(this.bucketName, this.endpoint),
      );

      // 检查文件是否存在
      logger.info(Messages.OSS_CHECK_FILE_EXISTS(localFile));
      const fileExists = fs.existsSync(localFile);
      logger.info(Messages.OSS_FILE_EXISTS_RESULT(fileExists));

      if (!fileExists) {
        throw BusinessException.notFound(
          Messages.OSS_LOCAL_FILE_NOT_FOUND(localFile),
        );
      }

      // 获取文件大小
      const stats = fs.statSync(localFile);
      logger.info(Messages.OSS_LOCAL_FILE_SIZE(stats.size));

      // 添加超时控制
      logger.info(Messages.OSS_PUT_OPERATION_START);
      const result = this.isBunRuntime()
        ? await this.uploadFileWithBun(localFile, ossFile)
        : await this.uploadFileWithAliOss(localFile, ossFile);

      logger.info(
        Messages.OSS_PUT_RESULT_INFO(JSON.stringify(result)),
      );

      const url: string = this.getFileUrl(ossFile);
      logger.info(Messages.OSS_FILE_UPLOAD_SUCCESS(url));
      return url;
    } catch (error: unknown) {
      const message: string =
        error instanceof Error ? error.message : String(error);
      logger.error(Messages.OSS_UPLOAD_ERROR_LOG(message));
      logger.error(
        Messages.OSS_UPLOAD_ERROR_DETAIL_INFO(localFile, ossFile),
      );
      logger.error(
        Messages.OSS_UPLOAD_ERROR_STACK_INFO(
          error instanceof Error ? error.stack || "" : "",
        ),
      );
      throw BusinessException.internalServerError(Messages.OSS_UPLOAD_FAILED);
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
      throw BusinessException.serviceUnavailable(
        Messages.OSS_CLIENT_NOT_INITIALIZED,
      );
    }

    const uploadPromise = this.client.put(ossFile, localFile);
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(
        () => reject(new Error(Messages.OSS_PUT_OPERATION_TIMEOUT)),
        this.putTimeout,
      ),
    );

    return Promise.race([uploadPromise, timeoutPromise]);
  }

  private async uploadFileWithBun(
    localFile: string,
    ossFile: string,
  ): Promise<unknown> {
    const fileBuffer = await fs.promises.readFile(localFile);
    const normalizedOssFile: string = ossFile.replace(/^\/+/, "");
    const requestPath: string = `/${this.bucketName}/${normalizedOssFile}`;
    const requestUrl: string = `https://${this.bucketName}.${this.endpoint}/${this.encodeOssPath(normalizedOssFile)}`;
    const contentType: string = Defaults.OSS_DEFAULT_CONTENT_TYPE;
    const requestDate: string = new Date().toUTCString();
    const stringToSign: string = [
      Defaults.OSS_HTTP_PUT_METHOD,
      "",
      contentType,
      requestDate,
      requestPath,
    ].join("\n");
    const signature: string = crypto
      .createHmac("sha1", this.accessKeySecret)
      .update(stringToSign)
      .digest("base64");
    const timeoutController = new AbortController();
    const timeoutId = setTimeout(
      () => timeoutController.abort(),
      this.putTimeout,
    );

    try {
      const response: Response = await fetch(requestUrl, {
        method: "PUT",
        headers: {
          Authorization: `OSS ${this.accessKeyId}:${signature}`,
          Date: requestDate,
          "Content-Type": contentType,
          "Content-Length": String(fileBuffer.byteLength),
        },
        body: new Uint8Array(fileBuffer),
        signal: timeoutController.signal,
      });

      if (!response.ok) {
        const responseText: string = await response.text();
        throw new Error(
          `${Messages.OSS_RESPONSE_NON_SUCCESS_PREFIX}: ${response.status} ${response.statusText}，${Messages.OSS_RESPONSE_CONTENT_PREFIX} ${responseText}`,
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
        throw BusinessException.gatewayTimeout(
          Messages.OSS_PUT_OPERATION_TIMEOUT,
        );
      }

      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  private encodeOssPath(ossFile: string): string {
    return ossFile
      .split("/")
      .map((segment: string) => encodeURIComponent(segment))
      .join("/");
  }
}
