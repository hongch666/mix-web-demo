import "reflect-metadata";
import { ValidationPipe } from "@nestjs/common";
import {
  ColumnConfigDto,
  SaveTableSettingsDto,
  TableKeyParamDto,
  TableSettingsQueryDto,
} from "./tableSettings.dto";

// 全局 ValidationPipe 的实际配置：开启 transform 与隐式类型转换
const pipe = new ValidationPipe({
  transform: true,
  transformOptions: { enableImplicitConversion: true },
});

describe("SaveTableSettingsDto", () => {
  // 验证合法列配置通过校验并完成嵌套类型转换
  it("验证合法列配置通过校验并完成嵌套转换", async () => {
    const dto = (await pipe.transform(
      {
        columns: [
          { key: "title", visible: true, order: 0, width: 200 },
          { key: "author", visible: false, order: 1 },
        ],
      },
      { type: "body" as const, metatype: SaveTableSettingsDto },
    )) as SaveTableSettingsDto;

    expect(dto.columns).toHaveLength(2);
    expect(dto.columns[0]).toBeInstanceOf(ColumnConfigDto);
    expect(dto.columns[0]?.key).toBe("title");
    expect(dto.columns[0]?.visible).toBe(true);
    expect(dto.columns[0]?.width).toBe(200);
    expect(dto.columns[1]?.width).toBeUndefined();
  });

  // 验证列配置不是数组被拒绝
  it("验证列配置不是数组被拒绝", async () => {
    await expect(
      pipe.transform(
        { columns: { key: "title" } },
        { type: "body" as const, metatype: SaveTableSettingsDto },
      ),
    ).rejects.toThrow();
  });

  // 验证嵌套列配置缺失列标识被拒绝
  it("验证嵌套列配置缺失key被拒绝", async () => {
    await expect(
      pipe.transform(
        { columns: [{ visible: true, order: 0 }] },
        { type: "body" as const, metatype: SaveTableSettingsDto },
      ),
    ).rejects.toThrow();
  });

  // 验证列配置为空数组时放行，是否拒绝空列表由业务层决定
  it("验证空列配置数组通过校验", async () => {
    const dto = (await pipe.transform(
      { columns: [] },
      { type: "body" as const, metatype: SaveTableSettingsDto },
    )) as SaveTableSettingsDto;

    expect(dto.columns).toEqual([]);
  });
});

describe("TableSettingsQueryDto", () => {
  // 验证查询参数中的 user_id 字符串被转换为数字
  it("验证查询参数 user_id 转换为数字", async () => {
    const dto = (await pipe.transform(
      { user_id: "9" },
      { type: "query" as const, metatype: TableSettingsQueryDto },
    )) as TableSettingsQueryDto;

    expect(dto.user_id).toBe(9);
  });

  // 验证缺省 user_id 时通过校验，由业务回退为当前登录用户
  it("验证缺省 user_id 时通过校验", async () => {
    const dto = (await pipe.transform(
      {},
      { type: "query" as const, metatype: TableSettingsQueryDto },
    )) as TableSettingsQueryDto;

    expect(dto.user_id).toBeUndefined();
  });

  // 验证非正整数的 user_id 被拒绝
  it("验证 user_id 为 0 时报错", async () => {
    await expect(
      pipe.transform(
        { user_id: "0" },
        { type: "query" as const, metatype: TableSettingsQueryDto },
      ),
    ).rejects.toThrow();
  });
});

describe("TableKeyParamDto", () => {
  // 验证常规页面标识通过校验，页面标识会参与缓存 key 拼接
  it("验证常规页面标识通过校验", async () => {
    const dto = (await pipe.transform(
      { table_key: "api-logs_v2" },
      { type: "param" as const, metatype: TableKeyParamDto },
    )) as TableKeyParamDto;

    expect(dto.table_key).toBe("api-logs_v2");
  });

  // 验证包含特殊字符的页面标识被拒绝，避免拼出异常缓存 key
  it("验证包含特殊字符的页面标识被拒绝", async () => {
    await expect(
      pipe.transform(
        { table_key: "articles:1" },
        { type: "param" as const, metatype: TableKeyParamDto },
      ),
    ).rejects.toThrow();
  });

  // 验证超长页面标识被拒绝
  it("验证超长页面标识被拒绝", async () => {
    await expect(
      pipe.transform(
        { table_key: "a".repeat(65) },
        { type: "param" as const, metatype: TableKeyParamDto },
      ),
    ).rejects.toThrow();
  });
});
