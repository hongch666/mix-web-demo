import * as fs from "node:fs";
import * as path from "node:path";

import { ConfigService } from "@nestjs/config";
import { BusinessException } from "src/common/exceptions/business.exception";
import { InternalTokenUtil } from "./internalToken.util";

const SECRET = "unit-test-internal-token-secret-32-bytes";

describe("InternalTokenUtil", () => {
  it("生成并解析内部令牌声明", async () => {
    const tokenUtil = createTokenUtil(resolveConfiguredSecret(), 60_000);

    const token = await tokenUtil.generateInternalToken(10001, "nestjs");
    const claims = await tokenUtil.validateInternalToken(token);

    console.log(`生成的内部Token: ${token}`);

    expect(claims).toMatchObject({
      userId: 10001,
      serviceName: "nestjs",
      tokenType: "internal",
    });
  });

  it("拒绝使用其他密钥签名的令牌", async () => {
    const issuer = createTokenUtil(SECRET, 60_000);
    const verifier = createTokenUtil(
      "another-unit-test-secret-with-32-bytes",
      60_000,
    );
    const token = await issuer.generateInternalToken(10001, "nestjs");

    await expect(verifier.validateInternalToken(token)).rejects.toBeInstanceOf(
      BusinessException,
    );
  });

  it("缺少密钥时拒绝初始化", () => {
    expect(() => createTokenUtil("", 60_000)).toThrow(BusinessException);
  });
});

function createTokenUtil(
  secret: string,
  expiration: number,
): InternalTokenUtil {
  const configService = {
    get: jest.fn((key: string) => {
      if (key === "internal-token.secret") {
        return secret;
      }
      if (key === "internal-token.expiration") {
        return expiration;
      }
      return undefined;
    }),
  } as unknown as ConfigService;
  return new InternalTokenUtil(configService);
}

function resolveConfiguredSecret(): string {
  const environmentSecret = process.env.INTERNAL_TOKEN_SECRET?.trim();
  if (environmentSecret) {
    return environmentSecret;
  }

  const candidates = [
    path.resolve(process.cwd(), ".env"),
    path.resolve(process.cwd(), "nestjs/.env"),
    path.resolve(process.cwd(), "../.env"),
  ];
  for (const candidate of candidates) {
    if (!fs.existsSync(candidate)) {
      continue;
    }
    const line = fs
      .readFileSync(candidate, "utf8")
      .split(/\r?\n/)
      .map((item) => item.trim())
      .find((item) => item.startsWith("INTERNAL_TOKEN_SECRET="));
    if (line) {
      const value = stripQuotes(line.slice(line.indexOf("=") + 1).trim());
      if (value) {
        return value;
      }
    }
  }
  return SECRET;
}

function stripQuotes(value: string): string {
  if (
    value.length >= 2 &&
    ((value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'")))
  ) {
    return value.slice(1, -1);
  }
  return value;
}
