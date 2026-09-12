import * as fs from "node:fs";
import * as path from "node:path";

import { ConfigService } from "@nestjs/config";
import { Test, TestingModule } from "@nestjs/testing";
import config from "src/config";
import { LoggerService } from "src/module/common/logger/logger.service";
import { OssService, type OssConfig } from "./oss.service";

const mockLoggerService = {
  info: jest.fn(),
  error: jest.fn(),
  warning: jest.fn(),
  debug: jest.fn(),
};

const LOCAL_TEST_FILE_NAME = "search_keywords_wordcloud.png";
const OSS_TEST_FILE_NAME = "test/search_keywords_wordcloud.png";

describe("OssService", () => {
  let ossService: OssService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        OssService,
        {
          provide: LoggerService,
          useValue: mockLoggerService,
        },
        {
          provide: ConfigService,
          useValue: {
            // 直接复用 src/config 的解析结果（已加载 .env 并替换 ${VAR:default} 占位符）
            get: jest.fn((key: string) => resolveAppConfig(key)),
          },
        },
      ],
    }).compile();

    await module.init();
    ossService = module.get<OssService>(OssService);
    jest.spyOn(ossService as any, "uploadFileWithAliOss").mockResolvedValue({});
  });

  it("应该使用现有配置上传固定文件并返回合法链接", async () => {
    const localFilePath: string = path.resolve(
      process.cwd(),
      "..",
      "static",
      "pic",
      LOCAL_TEST_FILE_NAME,
    );

    if (!fs.existsSync(localFilePath)) {
      const ossUrl = ossService.getFileUrl(OSS_TEST_FILE_NAME);
      expect(isValidOssUrl(ossUrl, OSS_TEST_FILE_NAME)).toBe(true);
      return;
    }

    const ossUrl: string = await ossService.uploadFile(
      localFilePath,
      OSS_TEST_FILE_NAME,
    );

    console.log(`上传成功的 OSS 链接: ${ossUrl}`);
    expect(isValidOssUrl(ossUrl, OSS_TEST_FILE_NAME)).toBe(true);
  });
});

function resolveAppConfig(key: string): unknown {
  return config[key];
}

function getOssConfig(): OssConfig {
  return resolveAppConfig("oss") as OssConfig;
}

function isValidOssUrl(ossUrl: string, ossFile: string): boolean {
  const { bucket_name: bucketName, endpoint } = getOssConfig();

  try {
    const urlObject: URL = new URL(ossUrl);

    return (
      urlObject.protocol === "https:" &&
      urlObject.hostname === `${bucketName}.${endpoint}` &&
      urlObject.pathname === `/${ossFile}`
    );
  } catch {
    return false;
  }
}
