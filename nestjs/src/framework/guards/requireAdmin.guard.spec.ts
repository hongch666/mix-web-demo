import { ExecutionContext } from "@nestjs/common";
import { Reflector } from "@nestjs/core";
import { ClsService } from "nestjs-cls";
import { BusinessException } from "src/common/exceptions/business.exception";
import { SpringClientService } from "src/module/common/client/springClient.service";
import { REQUIRE_ADMIN_KEY } from "../decorators/requireAdmin.decorator";
import { RequireAdminGuard } from "./requireAdmin.guard";

describe("RequireAdminGuard", () => {
  const handler = jest.fn();
  const context = {
    getHandler: () => handler,
  } as unknown as ExecutionContext;

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const { guard, springClient } = createGuard(false, undefined);

    await expect(guard.canActivate(context)).resolves.toBe(true);
    expect(springClient.isAdminUser).not.toHaveBeenCalled();
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const { guard, springClient } = createGuard(true, undefined);

    await expect(guard.canActivate(context)).rejects.toBeInstanceOf(
      BusinessException,
    );
    expect(springClient.isAdminUser).not.toHaveBeenCalled();
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const { guard, springClient } = createGuard(true, 7, { data: true });

    await expect(guard.canActivate(context)).resolves.toBe(true);
    expect(springClient.isAdminUser).toHaveBeenCalledWith(7);
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", async () => {
    const { guard } = createGuard(true, 7, { data: false });

    await expect(guard.canActivate(context)).rejects.toBeInstanceOf(
      BusinessException,
    );
  });
});

function createGuard(
  requireAdmin: boolean,
  userId: number | undefined,
  adminResult: Record<string, unknown> = { data: false },
): {
  guard: RequireAdminGuard;
  springClient: jest.Mocked<Pick<SpringClientService, "isAdminUser">>;
} {
  const reflector = {
    get: jest.fn((key: string) =>
      key === REQUIRE_ADMIN_KEY ? requireAdmin : undefined,
    ),
  } as unknown as Reflector;
  const cls = {
    get: jest.fn(() => userId),
  } as unknown as ClsService;
  const springClient = {
    isAdminUser: jest.fn().mockResolvedValue(adminResult),
  };
  return {
    guard: new RequireAdminGuard(
      reflector,
      cls,
      springClient as unknown as SpringClientService,
    ),
    springClient,
  };
}
