import "reflect-metadata";
import { ValidationPipe } from "@nestjs/common";
import { GithubAuthorizeQueryDto, GithubCallbackQueryDto } from "./github.dto";

// 全局 ValidationPipe 的实际配置：开启 transform 与隐式类型转换
const pipe = new ValidationPipe({
  transform: true,
  transformOptions: { enableImplicitConversion: true },
});

describe("GithubAuthorizeQueryDto", () => {
  // 验证回跳路径为可选字段，合法字符串通过校验
  it("验证合法回跳路径通过校验", async () => {
    const dto = (await pipe.transform(
      { redirect: "/profile" },
      { type: "query" as const, metatype: GithubAuthorizeQueryDto },
    )) as GithubAuthorizeQueryDto;

    expect(dto.redirect).toBe("/profile");
  });

  // 验证回跳路径缺省时校验放行，符合可选字段语义
  it("验证空查询对象通过校验", async () => {
    const dto = (await pipe.transform(
      {},
      { type: "query" as const, metatype: GithubAuthorizeQueryDto },
    )) as GithubAuthorizeQueryDto;

    expect(dto.redirect).toBeUndefined();
  });

  // 验证非字符串回跳路径被拒绝
  it("验证非字符串回跳路径被拒绝", async () => {
    await expect(
      pipe.transform(
        { redirect: ["/profile"] },
        { type: "query" as const, metatype: GithubAuthorizeQueryDto },
      ),
    ).rejects.toThrow();
  });
});

describe("GithubCallbackQueryDto", () => {
  // 验证正常授权回调携带完整字段时通过校验
  it("验证完整授权回调通过校验", async () => {
    const dto = (await pipe.transform(
      { code: "abc123", state: "state123" },
      { type: "query" as const, metatype: GithubCallbackQueryDto },
    )) as GithubCallbackQueryDto;

    expect(dto.code).toBe("abc123");
    expect(dto.state).toBe("state123");
  });

  // 验证用户拒绝授权时仅携带错误字段的回调同样放行，全部字段均可选
  // errorDescription 带 @ExposeName，请求键名为 snake_case 的 error_description
  it("验证仅携带错误字段的拒绝授权回调通过校验", async () => {
    const dto = (await pipe.transform(
      {
        error: "access_denied",
        error_description: "The user denied the request",
      },
      { type: "query" as const, metatype: GithubCallbackQueryDto },
    )) as GithubCallbackQueryDto;

    expect(dto.code).toBeUndefined();
    expect(dto.error).toBe("access_denied");
    expect(dto.errorDescription).toBe("The user denied the request");
  });

  // 验证数组输入无法隐式转换为字符串，被校验拒绝
  it("验证非字符串授权码被拒绝", async () => {
    await expect(
      pipe.transform(
        { code: ["abc123"] },
        { type: "query" as const, metatype: GithubCallbackQueryDto },
      ),
    ).rejects.toThrow();
  });
});
