/* eslint-disable @typescript-eslint/unbound-method */

import "reflect-metadata";
import { RequireAdmin, REQUIRE_ADMIN_KEY } from "./requireAdmin.decorator";

describe("RequireAdmin装饰器", () => {
  // 验证装饰器会写入管理员权限元数据
  it("验证写入管理员权限元数据", () => {
    class Fixture {
      @RequireAdmin()
      adminOnly(): void {}
    }
    expect(
      Reflect.getMetadata(REQUIRE_ADMIN_KEY, Fixture.prototype.adminOnly),
    ).toBe(true);
  });
});
