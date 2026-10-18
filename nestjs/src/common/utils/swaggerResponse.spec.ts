import { DECORATORS } from "@nestjs/swagger/dist/constants";
import "reflect-metadata";
import { ApiRedirectResponse, ApiResponseModel } from "./swaggerResponse";

type MetadataRecord = Record<string, unknown>;

// 取装饰器写入的 Swagger 响应声明，按状态码分组
const getResponseMetadata = (
  fixture: { prototype: unknown },
  method: string,
): Record<string, MetadataRecord> =>
  Reflect.getMetadata(
    DECORATORS.API_RESPONSE,
    (fixture.prototype as Record<string, unknown>)[method] as object,
  ) as Record<string, MetadataRecord>;

// 按状态码取单条响应声明
const byStatus = (
  responses: Record<string, MetadataRecord>,
  status: number,
): MetadataRecord => responses[String(status)] as MetadataRecord;

describe("ApiResponseModel装饰器", () => {
  // 验证默认参数下声明统一响应体结构
  it("默认参数声明统一响应体结构", () => {
    class Fixture {
      @ApiResponseModel()
      list(): void {}
    }
    const responses = getResponseMetadata(Fixture, "list");
    expect(Object.keys(responses)).toEqual(["200"]);
    const schema = byStatus(responses, 200).schema as Record<string, unknown>;
    expect(byStatus(responses, 200).description).toBe("成功");
    expect(schema.required).toEqual(["code", "msg", "data"]);
    expect(schema.properties).toEqual({
      code: {
        type: "integer",
        format: "int32",
        example: 200,
        description: "响应码，与 HTTP 状态码一致",
      },
      msg: { type: "string", example: "success", description: "响应消息" },
      data: { type: "object", description: "返回数据" },
    });
  });

  // 验证自定义 status 与 description 透传到响应声明
  it("自定义 status 与 description 透传", () => {
    class Fixture {
      @ApiResponseModel({ status: 201, description: "创建成功" })
      create(): void {}
    }
    const responses = getResponseMetadata(Fixture, "create");
    expect(Object.keys(responses)).toEqual(["201"]);
    expect(byStatus(responses, 201).description).toBe("创建成功");
  });

  // 验证嵌套 properties 的字段描述递归补齐且不覆盖已有描述
  it("嵌套 properties 递归补齐字段描述", () => {
    class Fixture {
      @ApiResponseModel({
        data: {
          type: "object",
          properties: {
            keywords: { type: "array", items: { type: "string" } },
            nested: {
              type: "object",
              description: "已有描述",
              properties: { name: { type: "string" } },
            },
          },
        },
      })
      list(): void {}
    }
    const schema = byStatus(getResponseMetadata(Fixture, "list"), 200)
      .schema as Record<string, unknown>;
    const data = (schema.properties as Record<string, unknown>).data as Record<
      string,
      unknown
    >;
    const properties = data.properties as Record<string, unknown>;
    expect(data.description).toBe("返回数据");
    expect((properties.keywords as Record<string, unknown>).description).toBe(
      "keywords字段",
    );
    expect((properties.keywords as Record<string, unknown>).items).toEqual({
      type: "string",
      description: "列表项",
    });
    expect((properties.nested as Record<string, unknown>).description).toBe(
      "已有描述",
    );
    const nestedProperties = (properties.nested as Record<string, unknown>)
      .properties as Record<string, unknown>;
    expect((nestedProperties.name as Record<string, unknown>).description).toBe(
      "name字段",
    );
  });

  // 验证数组 items 的列表项描述递归补齐
  it("数组 items 递归补齐列表项描述", () => {
    class Fixture {
      @ApiResponseModel({
        data: {
          type: "array",
          items: {
            type: "object",
            properties: { name: { type: "string" } },
          },
        },
      })
      list(): void {}
    }
    const schema = byStatus(getResponseMetadata(Fixture, "list"), 200)
      .schema as Record<string, unknown>;
    const data = (schema.properties as Record<string, unknown>).data as Record<
      string,
      unknown
    >;
    const items = data.items as Record<string, unknown>;
    expect(items.description).toBe("列表项");
    const itemProperties = items.properties as Record<string, unknown>;
    expect((itemProperties.name as Record<string, unknown>).description).toBe(
      "name字段",
    );
  });
});

describe("ApiRedirectResponse装饰器", () => {
  // 验证默认声明 302 与 Location 响应头
  it("默认声明 302 与 Location 响应头", () => {
    class Fixture {
      @ApiRedirectResponse()
      redirect(): void {}
    }
    const responses = getResponseMetadata(Fixture, "redirect");
    expect(Object.keys(responses)).toEqual(["302"]);
    const meta = byStatus(responses, 302);
    expect(meta.description).toBe("重定向");
    const headers = meta.headers as Record<string, unknown>;
    expect((headers.Location as Record<string, unknown>).schema).toEqual({
      type: "string",
    });
  });

  // 验证自定义 description 与 status 透传
  it("自定义 description 与 status 透传", () => {
    class Fixture {
      @ApiRedirectResponse("跳转到授权页", 301)
      redirect(): void {}
    }
    const responses = getResponseMetadata(Fixture, "redirect");
    expect(Object.keys(responses)).toEqual(["301"]);
    expect(byStatus(responses, 301).description).toBe("跳转到授权页");
  });
});
