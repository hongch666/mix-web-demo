import { ExecutionContext } from "@nestjs/common";
import { Reflector } from "@nestjs/core";
import { ClsService } from "nestjs-cls";
import { ErrorIds, HttpCode } from "src/common/constants";
import { BusinessException } from "src/common/exceptions/business.exception";
import { SpringClientService } from "src/module/common/client/springClient.service";
import { LoggerService } from "src/module/common/logger/logger.service";
import {
  REQUIRE_SELF_KEY,
  REQUIRE_SELF_OPTIONS_KEY,
  type RequireSelfOptions,
} from "../decorators/requireSelf.decorator";
import { RequireSelfGuard } from "./requireSelf.guard";

/**
 * 守卫测试夹具，包含守卫实例、依赖 Mock 与对应的执行上下文
 */
interface GuardFixture {
  guard: RequireSelfGuard;
  springClient: { isAdminUser: jest.Mock };
  cls: { get: jest.Mock };
  context: ExecutionContext;
}

/**
 * 构造守卫及其依赖，默认场景为已标注装饰器的查询参数校验
 */
function createGuard(scenario: {
  requireSelf?: boolean;
  options?: RequireSelfOptions;
  userId?: number;
  query?: Record<string, unknown>;
  params?: Record<string, unknown>;
  body?: Record<string, unknown>;
  adminResult?: Record<string, unknown>;
  adminError?: Error;
}): GuardFixture {
  const metadata: Record<string, unknown> = {
    [REQUIRE_SELF_KEY]: scenario.requireSelf ?? true,
    [REQUIRE_SELF_OPTIONS_KEY]: scenario.options ?? {},
  };
  const reflector = {
    getAllAndOverride: jest.fn((key: string) => metadata[key]),
  } as unknown as Reflector;

  const cls = {
    get: jest.fn(() => scenario.userId),
  };
  const request = {
    query: scenario.query ?? {},
    params: scenario.params ?? {},
    body: scenario.body ?? {},
  };
  const context = {
    getHandler: () => "handler",
    getClass: () => "controller",
    switchToHttp: () => ({ getRequest: () => request }),
  } as unknown as ExecutionContext;

  const springClient = {
    isAdminUser:
      scenario.adminError !== undefined
        ? jest.fn().mockRejectedValue(scenario.adminError)
        : jest.fn().mockResolvedValue(scenario.adminResult ?? { data: false }),
  };
  const logger = {
    info: jest.fn(),
    warning: jest.fn(),
    error: jest.fn(),
  };

  return {
    guard: new RequireSelfGuard(
      reflector,
      cls as unknown as ClsService,
      springClient as unknown as SpringClientService,
      logger as unknown as LoggerService,
    ),
    springClient,
    cls,
    context,
  };
}

/**
 * 捕获守卫抛出的异常，便于断言状态码与错误标识
 */
async function captureError(
  guard: RequireSelfGuard,
  context: ExecutionContext,
): Promise<BusinessException> {
  try {
    await guard.canActivate(context);
  } catch (error: unknown) {
    if (error instanceof BusinessException) {
      return error;
    }
    throw error;
  }
  throw new Error("守卫未按预期抛出业务异常");
}

describe("RequireSelfGuard", () => {
  it("should_skip_check_when_handler_is_not_decorated", async () => {
    const { guard, springClient, context } = createGuard({
      requireSelf: false,
    });

    await expect(guard.canActivate(context)).resolves.toBe(true);
    expect(springClient.isAdminUser).not.toHaveBeenCalled();
  });

  it("should_throw_unauthorized_when_user_context_missing", async () => {
    const { guard, springClient, context } = createGuard({ userId: undefined });

    const error = await captureError(guard, context);
    expect(error.getStatus()).toBe(HttpCode.UNAUTHORIZED);
    expect(springClient.isAdminUser).not.toHaveBeenCalled();
  });

  it("should_allow_self_and_skip_admin_lookup", async () => {
    const { guard, springClient, context } = createGuard({
      userId: 7,
      query: { user_id: "7" },
    });

    await expect(guard.canActivate(context)).resolves.toBe(true);
    expect(springClient.isAdminUser).not.toHaveBeenCalled();
  });

  it("should_fallback_to_current_user_when_target_missing", async () => {
    const { guard, springClient, context } = createGuard({ userId: 7 });

    await expect(guard.canActivate(context)).resolves.toBe(true);
    expect(springClient.isAdminUser).not.toHaveBeenCalled();
  });

  it("should_allow_admin_accessing_other_user", async () => {
    const { guard, springClient, context } = createGuard({
      userId: 7,
      query: { user_id: "9" },
      adminResult: { data: true },
    });

    await expect(guard.canActivate(context)).resolves.toBe(true);
    expect(springClient.isAdminUser).toHaveBeenCalledWith(7);
  });

  it("should_forbidden_when_normal_user_accessing_other_user", async () => {
    const { guard, springClient, context } = createGuard({
      userId: 7,
      query: { user_id: "9" },
      adminResult: { data: false },
    });

    const error = await captureError(guard, context);
    expect(error.getStatus()).toBe(HttpCode.FORBIDDEN);
    expect(error.getErrorIdentifier()).toBe(ErrorIds.SELF_OR_ADMIN_REQUIRED);
    expect(springClient.isAdminUser).toHaveBeenCalledWith(7);
  });

  it("should_throw_bad_request_when_target_user_id_invalid", async () => {
    const { guard, springClient, context } = createGuard({
      userId: 7,
      query: { user_id: "0" },
    });

    const error = await captureError(guard, context);
    expect(error.getStatus()).toBe(HttpCode.BAD_REQUEST);
    expect(error.getErrorIdentifier()).toBe(ErrorIds.USER_SCOPE_TARGET_INVALID);
    expect(springClient.isAdminUser).not.toHaveBeenCalled();
  });

  it("should_fail_closed_when_admin_check_throws", async () => {
    const { guard, context } = createGuard({
      userId: 7,
      query: { user_id: "9" },
      adminError: new Error("spring 不可用"),
    });

    const error = await captureError(guard, context);
    expect(error.getStatus()).toBe(HttpCode.INTERNAL_SERVER_ERROR);
    expect(error.getErrorIdentifier()).toBe(
      ErrorIds.ADMIN_PERMISSION_CHECK_FAILED,
    );
  });

  it("should_resolve_target_from_path_param_when_configured", async () => {
    const { guard, springClient, context } = createGuard({
      userId: 7,
      options: { source: "param", paramName: "user_id" },
      params: { user_id: "7" },
    });

    await expect(guard.canActivate(context)).resolves.toBe(true);
    expect(springClient.isAdminUser).not.toHaveBeenCalled();
  });
});
