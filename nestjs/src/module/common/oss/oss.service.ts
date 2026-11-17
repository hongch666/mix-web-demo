import { Inject, Injectable, OnModuleInit, Optional } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";
import * as crypto from "crypto";
import * as fs from "fs";
import { Defaults, Messages } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { LoggerService } from "src/module/common/logger/logger.service";
import { OSS_CLIENT } from "./oss.tokens";

/**
 * 阿里云 OSS 配置结构，包含访问密钥、存储桶名称与访问端点
 */
export interface OssConfig {
  access_key_id: string;
  access_key_secret: string;
  bucket_name: string;
  endpoint: string;
}

/**
 * OSS 对象简要信息，列取接口返回
 */
export interface OssObjectInfo {
  /** 对象 key（不含 bucket 域名） */
  name: string;
  /** 对象字节数 */
  size?: number;
}

/**
 * OSS 列取一页的结果
 */
export interface OssListPage {
  /** 本页对象列表 */
  objects: OssObjectInfo[];
  /** 下一页游标，为空表示已列取完毕 */
  nextMarker: string | null;
}

/**
 * ali-oss list 接口的选项
 */
export interface OssListOptions {
  prefix?: string;
  marker?: string;
  "max-keys"?: number;
}

/**
 * ali-oss list 接口的原始返回结构
 */
export interface OssListRawResult {
  objects?: Array<{ name?: string; size?: number }>;
  isTruncated?: boolean;
  nextMarker?: string;
}

/**
 * OSS 客户端最小接口，形状与 ali-oss 原生方法对齐，便于注入与单测打桩
 */
export interface OssClient {
  put(name: string, file: string): Promise<unknown>;
  list(options: OssListOptions): Promise<OssListRawResult>;
  del(keys: string[]): Promise<unknown>;
}

/**
 * OSS 文件上传服务，负责本地文件上传到阿里云对象存储并生成访问 URL，兼容 Node 与 Bun 运行时
 */
@Injectable()
export class OssService implements OnModuleInit {
  private client: OssClient | null = null;
  private bucketName!: string;
  private endpoint!: string;
  private accessKeyId!: string;
  private accessKeySecret!: string;
  private putTimeout!: number;

  constructor(
    private readonly configService: ConfigService,
    private readonly logger: LoggerService,
    @Optional()
    @Inject(OSS_CLIENT)
    private readonly ossClient: OssClient | null = null,
  ) {}

  /**
   * 模块初始化时读取并校验 OSS 配置，计算上传超时时间并记录 Bun 运行时兼容提示
   */
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
      (config["put_timeout"] as string) || (config["putTimeout"] as string),
    );
    this.putTimeout = Math.max(putTimeoutSec, 10) * 1000; // 最少 10 秒

    this.client = this.ossClient;
    if (this.isBunRuntime()) {
      this.logger.info(Messages.OSS_BUN_RUNTIME_COMPAT_MESSAGE);
    }
  }

  /**
   * 上传本地文件到 OSS
   * @param localFile 本地绝对路径
   * @param ossFile OSS 目标路径（例如："articles/xxx.docx"）
   */
  async uploadFile(localFile: string, ossFile: string): Promise<string> {
    try {
      this.logger.info(Messages.OSS_UPLOAD_START_DETAIL(localFile, ossFile));
      this.logger.info(
        Messages.OSS_CLIENT_CONFIG_INFO(this.bucketName, this.endpoint),
      );

      // 检查文件是否存在
      this.logger.info(Messages.OSS_CHECK_FILE_EXISTS(localFile));
      try {
        await fs.promises.access(localFile);
      } catch {
        throw BusinessException.notFound(
          Messages.OSS_LOCAL_FILE_NOT_FOUND(localFile),
        );
      }
      this.logger.info(Messages.OSS_FILE_EXISTS_RESULT(true));

      // 获取文件大小
      const stats = await fs.promises.stat(localFile);
      this.logger.info(Messages.OSS_LOCAL_FILE_SIZE(stats.size));

      // 添加超时控制
      this.logger.info(Messages.OSS_PUT_OPERATION_START);
      const result = this.isBunRuntime()
        ? await this.uploadFileWithBun(localFile, ossFile)
        : await this.uploadFileWithAliOss(localFile, ossFile);

      this.logger.info(Messages.OSS_PUT_RESULT_INFO(JSON.stringify(result)));

      const url: string = this.getFileUrl(ossFile);
      this.logger.info(Messages.OSS_FILE_UPLOAD_SUCCESS(url));
      return url;
    } catch (error: unknown) {
      const message: string =
        error instanceof Error ? error.message : String(error);
      this.logger.error(Messages.OSS_UPLOAD_ERROR_LOG(message));
      this.logger.error(
        Messages.OSS_UPLOAD_ERROR_DETAIL_INFO(localFile, ossFile),
      );
      this.logger.error(
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

  /**
   * 当前 bucket 的完整 URL 前缀，用于把完整 URL 反解成对象 key
   */
  getUrlPrefix(): string {
    return `https://${this.bucketName}.${this.endpoint}/`;
  }

  /**
   * 列取指定前缀下的全部对象 key，内部循环分页直到游标为空
   */
  async listObjects(prefix: string): Promise<OssObjectInfo[]> {
    if (!this.client) {
      throw BusinessException.serviceUnavailable(
        Messages.OSS_CLIENT_NOT_INITIALIZED,
      );
    }
    this.logger.info(Messages.OSS_LIST_START(prefix));
    const objects: OssObjectInfo[] = [];
    let marker = "";
    do {
      const page: OssListPage = this.isBunRuntime()
        ? await this.listObjectsWithBun(prefix, marker)
        : await this.listObjectsWithAliOss(prefix, marker);
      objects.push(...page.objects);
      marker = page.nextMarker ?? "";
    } while (marker);
    this.logger.info(Messages.OSS_LIST_COMPLETED(objects.length));
    return objects;
  }

  /**
   * 批量删除对象 key，空数组直接返回
   */
  async deleteObjects(keys: string[]): Promise<number> {
    if (keys.length === 0) {
      return 0;
    }
    if (!this.client) {
      throw BusinessException.serviceUnavailable(
        Messages.OSS_CLIENT_NOT_INITIALIZED,
      );
    }
    this.logger.info(Messages.OSS_DELETE_START(keys.length));
    if (this.isBunRuntime()) {
      await this.deleteObjectsWithBun(keys);
    } else {
      await this.client.del(keys);
    }
    this.logger.info(Messages.OSS_DELETE_COMPLETED(keys.length));
    return keys.length;
  }

  /**
   * 从完整 URL 解析出对象 key，仅接受当前 bucket 域名，其余返回 null
   */
  extractKey(url: string | null | undefined): string | null {
    if (!url) {
      return null;
    }
    const prefix: string = this.getUrlPrefix();
    if (!url.startsWith(prefix)) {
      this.logger.info(Messages.OSS_URL_HOST_SKIPPED(url));
      return null;
    }
    const key: string | undefined = url
      .substring(prefix.length)
      .split(/[?#]/)[0];
    return key ? decodeURIComponent(key) : null;
  }

  /**
   * 判断对象 key 是否属于允许清理的前缀白名单
   */
  isAllowedCleanupKey(key: string): boolean {
    const allowed: boolean = Defaults.OSS_CLEANUP_KEY_PREFIXES.some((prefix) =>
      key.startsWith(prefix),
    );
    if (!allowed) {
      this.logger.info(Messages.OSS_KEY_PREFIX_SKIPPED(key));
    }
    return allowed;
  }

  /**
   * 判断当前进程是否运行在 Bun 运行时环境
   */
  private isBunRuntime(): boolean {
    return Boolean(
      (process as NodeJS.Process & { versions?: { bun?: string } }).versions
        ?.bun,
    );
  }

  /**
   * 使用 ali-oss 客户端上传文件，并通过 Promise 竞争实现上传超时控制
   */
  private async uploadFileWithAliOss(
    localFile: string,
    ossFile: string,
  ): Promise<unknown> {
    if (!this.client) {
      throw BusinessException.serviceUnavailable(
        Messages.OSS_CLIENT_NOT_INITIALIZED,
      );
    }

    const uploadPromise: Promise<unknown> = this.client.put(ossFile, localFile);
    const timeoutPromise: Promise<never> = new Promise((_, reject) =>
      setTimeout(
        () => reject(new Error(Messages.OSS_PUT_OPERATION_TIMEOUT)),
        this.putTimeout,
      ),
    );

    return Promise.race([uploadPromise, timeoutPromise]);
  }

  /**
   * 在 Bun 环境下绕过 ali-oss，手工构造 OSS 签名并以 fetch PUT 方式上传文件
   */
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

  /**
   * 按路径分段对 OSS 目标路径做 URL 编码，保留路径分隔符
   */
  private encodeOssPath(ossFile: string): string {
    return ossFile
      .split("/")
      .map((segment: string) => encodeURIComponent(segment))
      .join("/");
  }

  /**
   * 使用 ali-oss 客户端列取一页对象
   */
  private async listObjectsWithAliOss(
    prefix: string,
    marker: string,
  ): Promise<OssListPage> {
    const result = await this.client!.list({
      prefix,
      marker,
      "max-keys": Defaults.OSS_LIST_PAGE_SIZE,
    });
    const objects: OssObjectInfo[] = (result.objects ?? [])
      .filter((item) => Boolean(item.name))
      .map((item) => ({ name: item.name!, size: item.size }));
    return {
      objects,
      nextMarker: result.isTruncated ? result.nextMarker || null : null,
    };
  }

  /**
   * 在 Bun 环境下用手工签名的 ListObjectsV2 请求列取一页对象
   */
  private async listObjectsWithBun(
    prefix: string,
    marker: string,
  ): Promise<OssListPage> {
    const params: Array<[string, string]> = [
      ["list-type", "2"],
      ["max-keys", String(Defaults.OSS_LIST_PAGE_SIZE)],
      ["prefix", prefix],
    ];
    if (marker) {
      params.push(["continuation-token", marker]);
    }
    // OSS V1 签名要求子资源按字典序参与 CanonicalizedResource
    params.sort((left, right) => left[0].localeCompare(right[0]));
    const query: string = params
      .map(
        ([key, value]) =>
          `${encodeURIComponent(key)}=${encodeURIComponent(value)}`,
      )
      .join("&");
    const canonicalResource = `/${this.bucketName}/?${query}`;
    const requestUrl = `https://${this.bucketName}.${this.endpoint}/?${query}`;
    const requestDate: string = new Date().toUTCString();
    const signature: string = this.signBunRequest(
      "GET",
      canonicalResource,
      requestDate,
    );
    const response: Response = await fetch(requestUrl, {
      method: "GET",
      headers: {
        Authorization: `OSS ${this.accessKeyId}:${signature}`,
        Date: requestDate,
      },
    });
    if (!response.ok) {
      throw new Error(
        `${Messages.OSS_RESPONSE_NON_SUCCESS_PREFIX}: ${response.status} ${response.statusText}`,
      );
    }
    return this.parseListObjectsXml(await response.text());
  }

  /**
   * 在 Bun 环境下用手工签名的 DELETE 请求逐个删除对象（404 视为已删除）
   */
  private async deleteObjectsWithBun(keys: string[]): Promise<void> {
    for (const key of keys) {
      const normalized: string = key.replace(/^\/+/, "");
      const canonicalResource = `/${this.bucketName}/${normalized}`;
      const requestUrl = `https://${this.bucketName}.${this.endpoint}/${this.encodeOssPath(normalized)}`;
      const requestDate: string = new Date().toUTCString();
      const signature: string = this.signBunRequest(
        "DELETE",
        canonicalResource,
        requestDate,
      );
      const response: Response = await fetch(requestUrl, {
        method: "DELETE",
        headers: {
          Authorization: `OSS ${this.accessKeyId}:${signature}`,
          Date: requestDate,
        },
      });
      if (!response.ok && response.status !== 404) {
        throw new Error(
          `${Messages.OSS_RESPONSE_NON_SUCCESS_PREFIX}: ${response.status} ${response.statusText}`,
        );
      }
    }
  }

  /**
   * 按 OSS V1 规则对指定方法与规范资源生成签名
   */
  private signBunRequest(
    method: string,
    canonicalResource: string,
    date: string,
  ): string {
    const stringToSign: string = [method, "", "", date, canonicalResource].join(
      "\n",
    );
    return crypto
      .createHmac("sha1", this.accessKeySecret)
      .update(stringToSign)
      .digest("base64");
  }

  /**
   * 解析 OSS ListObjectsV2 返回的 XML，提取对象 key、大小与下一页游标
   */
  private parseListObjectsXml(xml: string): OssListPage {
    const objects: OssObjectInfo[] = [];
    const contentPattern = /<Contents>([\s\S]*?)<\/Contents>/g;
    let matched: RegExpExecArray | null = contentPattern.exec(xml);
    while (matched !== null) {
      const content: string | undefined = matched[1];
      const keyMatch = content ? /<Key>([\s\S]*?)<\/Key>/.exec(content) : null;
      const key: string | undefined = keyMatch?.[1];
      if (key) {
        const sizeMatch = content
          ? /<Size>([\s\S]*?)<\/Size>/.exec(content)
          : null;
        const size: string | undefined = sizeMatch?.[1];
        objects.push({
          name: this.decodeXmlText(key),
          size: size ? Number(size) : undefined,
        });
      }
      matched = contentPattern.exec(xml);
    }
    const tokenMatch =
      /<NextContinuationToken>([\s\S]*?)<\/NextContinuationToken>/.exec(xml);
    const token: string | undefined = tokenMatch?.[1];
    return {
      objects,
      nextMarker: token ? this.decodeXmlText(token) : null,
    };
  }

  /**
   * 反转义 OSS XML 中的实体字符
   */
  private decodeXmlText(text: string): string {
    return text
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">")
      .replace(/&quot;/g, '"')
      .replace(/&apos;/g, "'")
      .replace(/&amp;/g, "&");
  }
}
