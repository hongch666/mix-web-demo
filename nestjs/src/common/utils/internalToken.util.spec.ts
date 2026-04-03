import * as fs from 'node:fs';
import * as path from 'node:path';

import { ConfigService } from '@nestjs/config';
import { Test, TestingModule } from '@nestjs/testing';
import { InternalTokenUtil } from './internalToken.util';

describe('InternalTokenUtil', () => {
  let internalTokenUtil: InternalTokenUtil;

  const defaultInternalTokenSecret = 'abcdefghijklmnopqrstuvwxyz123456';
  const defaultInternalTokenExpiration = 60000;

  beforeAll(() => {
    loadDotEnv();
  });

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        InternalTokenUtil,
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn((key: string) => {
              if (key === 'internal-token.secret') {
                return resolveConfigValue(
                  'INTERNAL_TOKEN_SECRET',
                  defaultInternalTokenSecret,
                );
              }
              if (key === 'internal-token.expiration') {
                return Number(
                  resolveConfigValue(
                    'INTERNAL_TOKEN_EXPIRATION',
                    String(defaultInternalTokenExpiration),
                  ),
                );
              }
              return undefined;
            }),
          },
        },
      ],
    }).compile();

    internalTokenUtil = module.get<InternalTokenUtil>(InternalTokenUtil);
  });

  it('应该生成可用的内部Token', async () => {
    const token = await internalTokenUtil.generateInternalToken(
      10001,
      'nestjs',
    );

    console.log(`生成的内部Token: ${token}`);
    expect(token).toBeTruthy();
    expect(token.length).toBeGreaterThan(0);
  });

  it('应该使用环境变量中的内部Token校验通过', async () => {
    const token = process.env.INTERNAL_TOKEN_TEST_TOKEN;

    expect(token).toBeTruthy();

    const claims = await internalTokenUtil.validateInternalToken(
      token as string,
    );

    expect(claims.userId).toBeDefined();
    expect(claims.serviceName).toBeDefined();
    expect(claims.tokenType).toBe('internal');
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
