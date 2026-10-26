/* eslint-disable @typescript-eslint/unbound-method */

import "reflect-metadata";
import {
  RequireSelf,
  REQUIRE_SELF_KEY,
  REQUIRE_SELF_OPTIONS_KEY,
} from "./requireSelf.decorator";

describe("RequireSelf装饰器", () => {
  // 验证默认为本人或管理员校验并写入空的配置对象
  it("验证默认写入本人或管理员元数据", () => {
    class Fixture {
      @RequireSelf()
      selfOnly(): void {}
    }

    expect(
      Reflect.getMetadata(REQUIRE_SELF_KEY, Fixture.prototype.selfOnly),
    ).toBe(true);
    expect(
      Reflect.getMetadata(REQUIRE_SELF_OPTIONS_KEY, Fixture.prototype.selfOnly),
    ).toEqual({});
  });

  // 验证显式配置按来源与参数名原样写入元数据
  it("验证写入指定的来源与参数名", () => {
    class Fixture {
      @RequireSelf({ source: "param", paramName: "user_id" })
      selfByPath(): void {}
    }

    expect(
      Reflect.getMetadata(
        REQUIRE_SELF_OPTIONS_KEY,
        Fixture.prototype.selfByPath,
      ),
    ).toEqual({ source: "param", paramName: "user_id" });
  });

  // 验证装饰器可作用于类，供守卫按 getAllAndOverride 读取类级声明
  it("验证类级声明写入本人或管理员元数据", () => {
    @RequireSelf({ source: "body", paramName: "sender_id" })
    class Fixture {}

    expect(Reflect.getMetadata(REQUIRE_SELF_KEY, Fixture)).toBe(true);
    expect(Reflect.getMetadata(REQUIRE_SELF_OPTIONS_KEY, Fixture)).toEqual({
      source: "body",
      paramName: "sender_id",
    });
  });

  // 验证未标注时不会产生元数据，守卫据此跳过校验
  it("验证未标注的方法不存在元数据", () => {
    class Fixture {
      normal(): void {}
    }

    expect(
      Reflect.getMetadata(REQUIRE_SELF_KEY, Fixture.prototype.normal),
    ).toBeUndefined();
    expect(
      Reflect.getMetadata(REQUIRE_SELF_OPTIONS_KEY, Fixture.prototype.normal),
    ).toBeUndefined();
  });
});
