import "reflect-metadata";
import { ValidationPipe } from "@nestjs/common";
import { SqlQueryDto } from "./sqlQuery.dto";

// 全局 ValidationPipe 的实际配置：开启 transform 与隐式类型转换
const pipe = new ValidationPipe({
  transform: true,
  transformOptions: { enableImplicitConversion: true },
});

describe("SqlQueryDto", () => {
  // 验证合法的参数化SQL查询通过校验
  it("验证合法参数化SQL查询通过校验", async () => {
    const dto = (await pipe.transform(
      {
        query:
          "SELECT * FROM user_table_settings WHERE user_id = :userId LIMIT :limit",
        params: { userId: 1, limit: 10 },
      },
      { type: "body" as const, metatype: SqlQueryDto },
    )) as SqlQueryDto;

    expect(dto.query).toContain(":userId");
    expect(dto.params).toEqual({ userId: 1, limit: 10 });
  });

  // 验证可选的参数键值对缺省时放行
  it("验证参数键值对缺省通过校验", async () => {
    const dto = (await pipe.transform(
      { query: "SELECT COUNT(*) FROM articles LIMIT 1" },
      { type: "body" as const, metatype: SqlQueryDto },
    )) as SqlQueryDto;

    expect(dto.params).toBeUndefined();
  });

  // 验证SQL语句为空被拒绝
  it("验证空SQL语句被拒绝", async () => {
    await expect(
      pipe.transform(
        { query: "" },
        { type: "body" as const, metatype: SqlQueryDto },
      ),
    ).rejects.toThrow();
  });

  // 验证参数键值对不是对象被拒绝
  it("验证非对象参数键值对被拒绝", async () => {
    await expect(
      pipe.transform(
        { query: "SELECT 1 LIMIT 1", params: "userId=1" },
        { type: "body" as const, metatype: SqlQueryDto },
      ),
    ).rejects.toThrow();
  });
});
