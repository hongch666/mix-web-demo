import * as fs from "node:fs";

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

  it("使用假配置初始化并生成文件地址", async () => {
    const service = createService(OSS_CONFIG, logger);
    mockBunRuntime(service);

    await service.onModuleInit();

    expect(service.getFileUrl("articles/test.docx")).toBe(
      "https://unit-test-bucket.oss-cn-test.aliyuncs.com/articles/test.docx",
    );
  });

  it("配置不完整时拒绝初始化", async () => {
    const service = createService({}, logger);

    await expect(service.onModuleInit()).rejects.toBeInstanceOf(
      BusinessException,
    );
  });

  it("上传本地文件时调用运行时适配器并返回文件地址", async () => {
    const service = createService(OSS_CONFIG, logger);
    mockBunRuntime(service);
    await service.onModuleInit();

    const bunUpload = jest
      .spyOn(service as never, "uploadFileWithBun" as never)
      .mockResolvedValue({} as never);
    jest.spyOn(fs.promises, "access").mockResolvedValue(undefined);
    jest.spyOn(fs.promises, "stat").mockResolvedValue({ size: 9 } as fs.Stats);
    const localFile = "C:/unit-test/upload.txt";

    const url = await service.uploadFile(localFile, "test/upload.txt");

    expect(url).toBe(
      "https://unit-test-bucket.oss-cn-test.aliyuncs.com/test/upload.txt",
    );
    expect(bunUpload).toHaveBeenCalledWith(localFile, "test/upload.txt");
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

function mockBunRuntime(service: OssService): void {
  jest
    .spyOn(
      service as unknown as { isBunRuntime: () => boolean },
      "isBunRuntime",
    )
    .mockReturnValue(true);
}
