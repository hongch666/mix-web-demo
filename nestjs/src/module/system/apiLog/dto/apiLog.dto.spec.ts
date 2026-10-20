import "reflect-metadata";
import { ValidationPipe } from "@nestjs/common";
import { ApiMethod, CreateApiLogDto, QueryApiLogDto } from "./apiLog.dto";

// 全局 ValidationPipe 的实际配置：开启 transform 与隐式类型转换
const pipe = new ValidationPipe({
  transform: true,
  transformOptions: { enableImplicitConversion: true },
});

// 构造合法的接口日志消息体，测试中按需覆盖字段
// 带 @ExposeName 的字段请求键名为 snake_case
const validCreatePayload = () => ({
  user_id: 1,
  username: "admin",
  api_description: "获取用户信息",
  api_path: "/api/users/1",
  api_method: ApiMethod.GET,
  response_time: 100,
});

describe("CreateApiLogDto", () => {
  // 验证合法日志消息体通过校验
  it("验证合法日志消息体通过校验", async () => {
    const dto = (await pipe.transform(validCreatePayload(), {
      type: "body" as const,
      metatype: CreateApiLogDto,
    })) as CreateApiLogDto;

    expect(dto.userId).toBe(1);
    expect(dto.apiMethod).toBe(ApiMethod.GET);
    expect(dto.responseTime).toBe(100);
  });

  // 验证可选的查询与路径参数缺省时放行
  it("验证可选参数缺省通过校验", async () => {
    const dto = (await pipe.transform(validCreatePayload(), {
      type: "body" as const,
      metatype: CreateApiLogDto,
    })) as CreateApiLogDto;

    expect(dto.queryParams).toBeUndefined();
    expect(dto.pathParams).toBeUndefined();
    expect(dto.requestBody).toBeUndefined();
  });

  // 验证必填字段缺失被拒绝
  it("验证缺失用户ID被拒绝", async () => {
    const payload = validCreatePayload();
    delete (payload as Record<string, unknown>).user_id;

    await expect(
      pipe.transform(payload, {
        type: "body" as const,
        metatype: CreateApiLogDto,
      }),
    ).rejects.toThrow();
  });

  // 验证API方法超出枚举范围被拒绝
  it("验证非法API方法被拒绝", async () => {
    await expect(
      pipe.transform(
        { ...validCreatePayload(), api_method: "TRACE" },
        { type: "body" as const, metatype: CreateApiLogDto },
      ),
    ).rejects.toThrow();
  });

  // 验证响应时间非数字被拒绝
  it("验证非法响应时间被拒绝", async () => {
    await expect(
      pipe.transform(
        { ...validCreatePayload(), response_time: [100] },
        { type: "body" as const, metatype: CreateApiLogDto },
      ),
    ).rejects.toThrow();
  });
});

describe("QueryApiLogDto", () => {
  // 验证合法查询参数通过校验
  it("验证合法查询参数通过校验", async () => {
    const dto = (await pipe.transform(
      {
        user_id: "1",
        username: "admin",
        api_method: ApiMethod.POST,
        page: "2",
        size: "20",
      },
      { type: "query" as const, metatype: QueryApiLogDto },
    )) as QueryApiLogDto;

    expect(dto.userId).toBe("1");
    expect(dto.apiMethod).toBe(ApiMethod.POST);
    expect(dto.page).toBe("2");
    expect(dto.size).toBe("20");
  });

  // 验证全部字段可选，空查询对象放行
  it("验证空查询对象通过校验", async () => {
    const dto = (await pipe.transform(
      {},
      { type: "query" as const, metatype: QueryApiLogDto },
    )) as QueryApiLogDto;

    expect(dto.page).toBeUndefined();
  });

  // 验证分页参数不是数字字符串被拒绝
  it("验证非数字字符串页码被拒绝", async () => {
    await expect(
      pipe.transform(
        { page: "abc" },
        { type: "query" as const, metatype: QueryApiLogDto },
      ),
    ).rejects.toThrow();
  });

  // 验证查询的API方法超出枚举范围被拒绝
  it("验证非法查询API方法被拒绝", async () => {
    await expect(
      pipe.transform(
        { api_method: "TRACE" },
        { type: "query" as const, metatype: QueryApiLogDto },
      ),
    ).rejects.toThrow();
  });
});
