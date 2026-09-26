/* eslint-disable @typescript-eslint/unbound-method */

import "reflect-metadata";
import {
  RequireInternalToken,
  REQUIRE_INTERNAL_TOKEN_KEY,
  REQUIRE_INTERNAL_TOKEN_SERVICE_NAME_KEY,
} from "./requireInternalToken.decorator";

describe("RequireInternalToken装饰器", () => {
  // 验证装饰器会写入内部令牌和服务名称元数据
  it("验证写入内部令牌元数据", () => {
    class Fixture {
      @RequireInternalToken("spring")
      internalOnly(): void {}
    }
    expect(
      Reflect.getMetadata(
        REQUIRE_INTERNAL_TOKEN_KEY,
        Fixture.prototype.internalOnly,
      ),
    ).toBe(true);
    expect(
      Reflect.getMetadata(
        REQUIRE_INTERNAL_TOKEN_SERVICE_NAME_KEY,
        Fixture.prototype.internalOnly,
      ),
    ).toBe("spring");
  });
});
