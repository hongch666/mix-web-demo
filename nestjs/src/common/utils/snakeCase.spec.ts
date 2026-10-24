import { instanceToPlain } from "class-transformer";
import { ExposeName, toSnakeCase } from "./snakeCase";

describe("snakeCase命名工具", () => {
  // 验证驼峰键名按大写字母逐个转为下划线
  it("验证驼峰键名转为下划线", () => {
    expect(toSnakeCase("userId")).toBe("user_id");
    expect(toSnakeCase("createdAt")).toBe("created_at");
  });

  // 验证无大写字母的键保持原样，避免对已符合契约的键重复转换
  it("验证无大写字母的键保持原样", () => {
    expect(toSnakeCase("user_id")).toBe("user_id");
    expect(toSnakeCase("user")).toBe("user");
  });

  // 验证连续大写字母被逐个拆分，固化该边界行为供调用方评估命名
  it("验证连续大写字母逐个拆分", () => {
    expect(toSnakeCase("myAPIKey")).toBe("my_a_p_i_key");
  });

  // 验证被装饰属性的序列化键名为下划线命名
  it("验证属性序列化为下划线名称", () => {
    class Dto {
      userId!: number;
    }
    ExposeName()(Dto.prototype, "userId");
    expect(instanceToPlain(Object.assign(new Dto(), { userId: 7 }))).toEqual({
      user_id: 7,
    });
  });

  // 验证 symbol 键降级为普通 Expose：不做名称映射，原键与原值均保留
  it("验证symbol键降级为普通Expose且不做名称映射", () => {
    class Dto {
      userId!: number;
    }
    const key = Symbol("userId");
    ExposeName()(Dto.prototype, key);
    const plain = instanceToPlain(
      Object.assign(new Dto(), { [key]: 7 }),
    ) as unknown as Record<symbol, unknown>;
    expect(plain[key]).toBe(7);
    expect(Object.keys(plain)).not.toContain("user_id");
  });
});
