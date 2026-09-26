import { CallHandler, ExecutionContext } from "@nestjs/common";
import { firstValueFrom, of } from "rxjs";
import { FieldNamingInterceptor } from "./fieldNaming.interceptor";

describe("FieldNamingInterceptor字段命名拦截器", () => {
  // 验证响应对象和数组会递归转换为下划线命名
  it("验证响应字段递归转换", async () => {
    const next: CallHandler = {
      handle: () =>
        of({
          userId: 1,
          items: [{ createdAt: "now" }],
          content: { rawKey: 1 },
        }),
    };
    const result = await firstValueFrom(
      new FieldNamingInterceptor().intercept({} as ExecutionContext, next),
    );
    expect(result).toEqual({
      user_id: 1,
      items: [{ created_at: "now" }],
      content: { rawKey: 1 },
    });
  });
});
