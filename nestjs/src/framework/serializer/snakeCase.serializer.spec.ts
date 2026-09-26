import { instanceToPlain } from "class-transformer";
import { ExposeName } from "./snakeCase.serializer";

describe("ExposeName序列化装饰器", () => {
  // 验证属性名称会序列化为下划线命名
  it("验证属性序列化为下划线名称", () => {
    class Dto {
      userId!: number;
    }
    ExposeName()(Dto.prototype, "userId");
    expect(instanceToPlain(Object.assign(new Dto(), { userId: 7 }))).toEqual({
      user_id: 7,
    });
  });
});
