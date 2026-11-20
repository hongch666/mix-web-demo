import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

import { ConfigService } from "@nestjs/config";
import { BusinessException } from "src/common/exceptions/business.exception";
import { LoggerService } from "src/module/common/logger/logger.service";
import { OssService } from "./oss.service";
import type { OssRuntime } from "./oss.tokens";

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

  // 验证批量删除调用 ali-oss 的 deleteMulti：6.x 已移除 del，旧实现会抛 TypeError
  it("验证批量删除调用 deleteMulti", async () => {
    const service = createConfiguredService();
    const deleteMulti = jest.fn().mockResolvedValue({ deleted: ["pic/a.png"] });
    Object.assign(service as unknown as Record<string, unknown>, {
      client: { put: jest.fn(), list: jest.fn(), deleteMulti },
    });

    await expect(service.deleteObjects(["pic/a.png"])).resolves.toBe(1);

    expect(deleteMulti).toHaveBeenCalledWith(["pic/a.png"], { quiet: true });
  });

  // 验证超过单次上限时按 1000 个分片调用，避免触发 OSS 批量删除限制
  it("验证批量删除按 1000 个分片调用", async () => {
    const service = createConfiguredService();
    const deleteMulti = jest.fn().mockResolvedValue({ deleted: [] });
    Object.assign(service as unknown as Record<string, unknown>, {
      client: { put: jest.fn(), list: jest.fn(), deleteMulti },
    });
    const keys: string[] = Array.from(
      { length: 1001 },
      (_, index) => `pic/${index}.png`,
    );

    await expect(service.deleteObjects(keys)).resolves.toBe(1001);

    expect(deleteMulti).toHaveBeenCalledTimes(2);
    expect(deleteMulti).toHaveBeenNthCalledWith(1, keys.slice(0, 1000), {
      quiet: true,
    });
    expect(deleteMulti).toHaveBeenNthCalledWith(2, keys.slice(1000), {
      quiet: true,
    });
  });

  // 验证 Bun 策略通过 fetch 删除对象，不调用 ali-oss 客户端
  it("验证 Bun 策略按 key 发起 DELETE 请求", async () => {
    const service = createConfiguredService("bun");
    Object.assign(service as unknown as Record<string, unknown>, {
      client: { put: jest.fn(), list: jest.fn(), deleteMulti: jest.fn() },
    });
    const deleteMulti = (
      service as unknown as { client: { deleteMulti: jest.Mock } }
    ).client.deleteMulti;
    const originalFetch: typeof fetch = globalThis.fetch;
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: "OK",
    } as Response);
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    try {
      await expect(service.deleteObjects(["pic/a.png"])).resolves.toBe(1);

      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(fetchMock).toHaveBeenCalledWith(
        "https://unit-test-bucket.oss-cn-test.aliyuncs.com/pic/a.png",
        expect.objectContaining({ method: "DELETE" }),
      );
      expect(deleteMulti).not.toHaveBeenCalled();
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});

function createService(
  ossConfig: Record<string, unknown>,
  logger: LoggerService,
  runtime: OssRuntime = "ali-oss",
): OssService {
  const configService = {
    get: jest.fn((key: string) => (key === "oss" ? ossConfig : undefined)),
  } as unknown as ConfigService;
  return new OssService(configService, logger, null, runtime);
}

function tCleanup(tempDir: string): void {
  try {
    fs.rmSync(tempDir, { recursive: true, force: true });
  } catch {
    // 测试进程会在退出时回收临时目录
  }
}

function createConfiguredService(runtime: OssRuntime = "ali-oss"): OssService {
  const service = createService(
    OSS_CONFIG,
    {
      info: jest.fn(),
      error: jest.fn(),
      warning: jest.fn(),
      debug: jest.fn(),
    } as unknown as LoggerService,
    runtime,
  );
  Object.assign(service as unknown as Record<string, unknown>, {
    bucketName: OSS_CONFIG.bucket_name,
    endpoint: OSS_CONFIG.endpoint,
    accessKeyId: OSS_CONFIG.access_key_id,
    accessKeySecret: OSS_CONFIG.access_key_secret,
    putTimeout: 10_000,
  });
  return service;
}
