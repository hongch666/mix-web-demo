import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

import { ConfigService } from "@nestjs/config";
import { BusinessException } from "src/common/exceptions/business.exception";
import { LoggerService } from "src/module/common/logger/logger.service";
import { OssService } from "./oss.service";

const OSS_CONFIG = {
  access_key_id: "unit-test-access-key",
  access_key_secret: "unit-test-access-secret",
  bucket_name: "unit-test-bucket",
  endpoint: "oss-cn-test.aliyuncs.com",
  put_timeout: "10",
};

describe("OssService", () => {
  const logger = {
    info: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
    debug: jest.fn(),
  } as unknown as LoggerService;

  afterEach(() => {
    jest.restoreAllMocks();
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const service = createConfiguredService();

    expect(service.getFileUrl("articles/test.docx")).toBe(
      "https://unit-test-bucket.oss-cn-test.aliyuncs.com/articles/test.docx",
    );
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const service = createService({}, logger);

    await expect(service.onModuleInit()).rejects.toBeInstanceOf(
      BusinessException,
    );
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const service = createConfiguredService();
    const uploadCalls: Array<[string, string]> = [];
    (
      service as unknown as {
        uploadFileWithAliOss: (
          localFile: string,
          ossFile: string,
        ) => Promise<unknown>;
        uploadFileWithBun: (
          localFile: string,
          ossFile: string,
        ) => Promise<unknown>;
      }
    ).uploadFileWithAliOss = async (localFile, ossFile) => {
      uploadCalls.push([localFile, ossFile]);
      return {};
    };
    (
      service as unknown as {
        uploadFileWithBun: (
          localFile: string,
          ossFile: string,
        ) => Promise<unknown>;
      }
    ).uploadFileWithBun = async (localFile, ossFile) => {
      uploadCalls.push([localFile, ossFile]);
      return {};
    };
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "oss-service-test-"));
    const localFile = path.join(tempDir, "upload.txt");
    fs.writeFileSync(localFile, "test file", "utf8");
    try {
      const url = await service.uploadFile(localFile, "test/upload.txt");
      expect(url).toBe(
        "https://unit-test-bucket.oss-cn-test.aliyuncs.com/test/upload.txt",
      );
      expect(uploadCalls).toEqual([[localFile, "test/upload.txt"]]);
    } finally {
      tCleanup(tempDir);
    }
  });
});

function createService(
  ossConfig: Record<string, unknown>,
  logger: LoggerService,
): OssService {
  const configService = {
    get: jest.fn((key: string) => (key === "oss" ? ossConfig : undefined)),
  } as unknown as ConfigService;
  return new OssService(configService, logger);
}

function tCleanup(tempDir: string): void {
  try {
    fs.rmSync(tempDir, { recursive: true, force: true });
  } catch {
    // 测试进程会在退出时回收临时目录
  }
}

function createConfiguredService(): OssService {
  const service = createService(OSS_CONFIG, {
    info: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
    debug: jest.fn(),
  } as unknown as LoggerService);
  Object.assign(service as unknown as Record<string, unknown>, {
    bucketName: OSS_CONFIG.bucket_name,
    endpoint: OSS_CONFIG.endpoint,
    accessKeyId: OSS_CONFIG.access_key_id,
    accessKeySecret: OSS_CONFIG.access_key_secret,
    putTimeout: 10_000,
  });
  return service;
}
