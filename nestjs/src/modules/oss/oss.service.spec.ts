import * as fs from 'node:fs';
import * as path from 'node:path';

import { ConfigService } from '@nestjs/config';
import { Test, TestingModule } from '@nestjs/testing';
import { OssService } from './oss.service';

const LOCAL_TEST_FILE_NAME = 'search_keywords_wordcloud.png';
const OSS_TEST_FILE_NAME = 'test/search_keywords_wordcloud.png';
const DEFAULT_BUCKET_NAME = 'mix-web-demo';
const DEFAULT_ENDPOINT = 'oss-cn-guangzhou.aliyuncs.com';

describe('OssService', () => {
  let ossService: OssService;

  beforeAll(() => {
    loadDotEnv();
  });

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        OssService,
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn((key: string) => {
              if (key === 'oss') {
                return {
                  access_key_id: resolveConfigValue('OSS_ACCESS_KEY_ID', ''),
                  access_key_secret: resolveConfigValue(
                    'OSS_ACCESS_KEY_SECRET',
                    '',
                  ),
                  bucket_name: resolveConfigValue(
                    'OSS_BUCKET_NAME',
                    DEFAULT_BUCKET_NAME,
                  ),
                  endpoint: resolveConfigValue(
                    'OSS_ENDPOINT',
                    DEFAULT_ENDPOINT,
                  ),
                };
              }

              return undefined;
            }),
          },
        },
      ],
    }).compile();

    await module.init();
    ossService = module.get<OssService>(OssService);
  });

  it('应该使用当前OSS配置上传固定文件并返回合法链接', async () => {
    const localFilePath: string = path.resolve(
      process.cwd(),
      '..',
      'static',
      'pic',
      LOCAL_TEST_FILE_NAME,
    );

    expect(fs.existsSync(localFilePath)).toBe(true);

    const ossUrl: string = await ossService.uploadFile(
      localFilePath,
      OSS_TEST_FILE_NAME,
    );

    console.log(`上传成功的 OSS 链接: ${ossUrl}`);
    expect(isValidOssUrl(ossUrl, OSS_TEST_FILE_NAME)).toBe(true);
  });
});

function loadDotEnv(): void {
  const candidates = [
    path.resolve(process.cwd(), '.env'),
    path.resolve(process.cwd(), 'nestjs/.env'),
    path.resolve(process.cwd(), '../.env'),
  ];

  for (const candidate of candidates) {
    if (!fs.existsSync(candidate)) {
      continue;
    }

    const content = fs.readFileSync(candidate, 'utf8');
    for (const line of content.split(/\r?\n/)) {
      const trimmedLine = line.trim();
      if (
        !trimmedLine ||
        trimmedLine.startsWith('#') ||
        !trimmedLine.includes('=')
      ) {
        continue;
      }

      const keyValueParts = trimmedLine.split('=');
      const rawKey = keyValueParts[0];
      if (!rawKey) {
        continue;
      }

      const key = rawKey.trim();
      const value = stripQuotes(keyValueParts.slice(1).join('=').trim());

      if (key && process.env[key] === undefined) {
        process.env[key] = value;
      }
    }

    break;
  }
}

function resolveConfigValue(key: string, defaultValue: string): string {
  const envValue = process.env[key];
  if (envValue && envValue.trim()) {
    return envValue.trim();
  }

  return defaultValue;
}

function stripQuotes(value: string): string {
  if (value.length >= 2) {
    const firstChar = value[0];
    const lastChar = value[value.length - 1];
    if (
      (firstChar === '"' && lastChar === '"') ||
      (firstChar === "'" && lastChar === "'")
    ) {
      return value.slice(1, -1);
    }
  }

  return value;
}

function isValidOssUrl(ossUrl: string, ossFile: string): boolean {
  try {
    const urlObject: URL = new URL(ossUrl);
    const bucketName: string = resolveConfigValue(
      'OSS_BUCKET_NAME',
      DEFAULT_BUCKET_NAME,
    );
    const endpoint: string = resolveConfigValue(
      'OSS_ENDPOINT',
      DEFAULT_ENDPOINT,
    );

    return (
      urlObject.protocol === 'https:' &&
      urlObject.hostname === `${bucketName}.${endpoint}` &&
      urlObject.pathname === `/${ossFile}`
    );
  } catch {
    return false;
  }
}
