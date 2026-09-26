import { ExecutionContext } from "@nestjs/common";
import { Reflector } from "@nestjs/core";
import { ClsService } from "nestjs-cls";
import { BusinessException } from "src/common/exceptions/business.exception";
import { InternalTokenUtil } from "src/common/utils/internalToken.util";
import { LoggerService } from "src/module/common/logger/logger.service";
import {
  REQUIRE_INTERNAL_TOKEN_KEY,
  REQUIRE_INTERNAL_TOKEN_SERVICE_NAME_KEY,
} from "../decorators/requireInternalToken.decorator";
import { InternalTokenGuard } from "./internalToken.guard";

describe("InternalTokenGuard", () => {
  const handler = jest.fn();
  const context = {
    getHandler: () => handler,
  } as unknown as ExecutionContext;

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const { guard, tokenUtil } = createGuard(false, "", undefined);

    await expect(guard.canActivate(context)).resolves.toBe(true);
    expect(tokenUtil.validateInternalToken).not.toHaveBeenCalled();
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const { guard } = createGuard(true, "", undefined);

    await expect(guard.canActivate(context)).rejects.toBeInstanceOf(
      BusinessException,
    );
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const { guard, tokenUtil } = createGuard(true, "token", "spring");
    tokenUtil.validateInternalToken.mockResolvedValue({
      userId: 9,
      serviceName: "spring",
      tokenType: "internal",
    });

    await expect(guard.canActivate(context)).resolves.toBe(true);
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const { guard, tokenUtil } = createGuard(true, "token", "spring");
    tokenUtil.validateInternalToken.mockResolvedValue({
      userId: 9,
      serviceName: "gozero",
      tokenType: "internal",
    });

    await expect(guard.canActivate(context)).rejects.toBeInstanceOf(
      BusinessException,
    );
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const { guard, tokenUtil } = createGuard(true, "token", undefined);
    tokenUtil.validateInternalToken.mockRejectedValue(new Error("invalid"));

    await expect(guard.canActivate(context)).rejects.toBeInstanceOf(
      BusinessException,
    );
  });
});

function createGuard(
  required: boolean,
  token: string,
  serviceName: string | undefined,
): {
  guard: InternalTokenGuard;
  tokenUtil: jest.Mocked<Pick<InternalTokenUtil, "validateInternalToken">>;
} {
  const reflector = {
    get: jest.fn((key: string) => {
      if (key === REQUIRE_INTERNAL_TOKEN_KEY) {
        return required;
      }
      if (key === REQUIRE_INTERNAL_TOKEN_SERVICE_NAME_KEY) {
        return serviceName;
      }
      return undefined;
    }),
  } as unknown as Reflector;
  const cls = { get: jest.fn(() => token) } as unknown as ClsService;
  const tokenUtil = { validateInternalToken: jest.fn() };
  const logger = {
    info: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
    debug: jest.fn(),
  } as unknown as LoggerService;
  return {
    guard: new InternalTokenGuard(
      reflector,
      cls,
      tokenUtil as unknown as InternalTokenUtil,
      logger,
    ),
    tokenUtil,
  };
}
