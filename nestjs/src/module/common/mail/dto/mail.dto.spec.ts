import "reflect-metadata";
import { ValidationPipe } from "@nestjs/common";
import { InternalEmailCodeSendDto } from "./mail.dto";

// 全局 ValidationPipe 的实际配置：开启 transform 与隐式类型转换
const pipe = new ValidationPipe({
  transform: true,
  transformOptions: { enableImplicitConversion: true },
});

// 构造合法的验证码发送请求体，测试中按需覆盖字段
const validPayload = () => ({
  email: "user@example.com",
  code: "123456",
  type: "register",
});

describe("InternalEmailCodeSendDto", () => {
  // 验证合法请求体通过校验，可选的过期时间缺省时保持 undefined
  it("验证合法请求体通过校验", async () => {
    const dto = (await pipe.transform(validPayload(), {
      type: "body" as const,
      metatype: InternalEmailCodeSendDto,
    })) as InternalEmailCodeSendDto;

    expect(dto.email).toBe("user@example.com");
    expect(dto.code).toBe("123456");
    expect(dto.type).toBe("register");
    expect(dto.expireMinutes).toBeUndefined();
  });

  // 验证可选的过期时间在范围内时通过校验
  // expireMinutes 带 @ExposeName，请求键名为 snake_case 的 expire_minutes
  it("验证合法过期时间通过校验", async () => {
    const dto = (await pipe.transform(
      { ...validPayload(), expire_minutes: 10 },
      { type: "body" as const, metatype: InternalEmailCodeSendDto },
    )) as InternalEmailCodeSendDto;

    expect(dto.expireMinutes).toBe(10);
  });

  // 验证邮箱格式错误被拒绝
  it("验证非法邮箱格式被拒绝", async () => {
    await expect(
      pipe.transform(
        { ...validPayload(), email: "not-an-email" },
        { type: "body" as const, metatype: InternalEmailCodeSendDto },
      ),
    ).rejects.toThrow();
  });

  // 验证必填字段缺失被拒绝
  it("验证缺失邮箱与验证码被拒绝", async () => {
    await expect(
      pipe.transform(
        { type: "register" },
        { type: "body" as const, metatype: InternalEmailCodeSendDto },
      ),
    ).rejects.toThrow();

    await expect(
      pipe.transform(
        { ...validPayload(), code: "" },
        { type: "body" as const, metatype: InternalEmailCodeSendDto },
      ),
    ).rejects.toThrow();
  });

  // 验证验证码场景超出枚举范围被拒绝
  it("验证非法验证码类型被拒绝", async () => {
    await expect(
      pipe.transform(
        { ...validPayload(), type: "unknown" },
        { type: "body" as const, metatype: InternalEmailCodeSendDto },
      ),
    ).rejects.toThrow();
  });

  // 验证过期时间小于 1 或非整数被拒绝
  it("验证非法过期时间被拒绝", async () => {
    await expect(
      pipe.transform(
        { ...validPayload(), expire_minutes: 0 },
        { type: "body" as const, metatype: InternalEmailCodeSendDto },
      ),
    ).rejects.toThrow();

    await expect(
      pipe.transform(
        { ...validPayload(), expire_minutes: "abc" },
        { type: "body" as const, metatype: InternalEmailCodeSendDto },
      ),
    ).rejects.toThrow();
  });
});
