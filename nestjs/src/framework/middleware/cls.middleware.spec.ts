import { ClsMiddleware } from "./cls.middleware";

describe("ClsMiddleware请求上下文中间件", () => {
  // 验证请求头会解析并写入CLS上下文
  it("验证请求头写入CLS上下文", () => {
    const values = new Map<string, unknown>();
    const cls = {
      set: jest.fn((key: string, value: unknown) => values.set(key, value)),
    };
    const next = jest.fn();
    new ClsMiddleware(cls as never).use(
      {
        headers: {
          "x-user-id": "7",
          "x-username": "alice",
          authorization: "Bearer token",
          "x-internal-token": "Bearer internal",
        },
      } as never,
      {} as never,
      next,
    );
    expect(values.get("userId")).toBe(7);
    expect(values.get("username")).toBe("alice");
    expect(values.get("token")).toBe("token");
    expect(values.get("internalToken")).toBe("internal");
    expect(next).toHaveBeenCalled();
  });
});
