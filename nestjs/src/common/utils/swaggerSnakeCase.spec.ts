/* eslint-disable @typescript-eslint/no-explicit-any */

import { applySwaggerSnakeCase } from "./swaggerSnakeCase";

describe("applySwaggerSnakeCase", () => {
  // Verify the expected behavior of this unit test
  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", () => {
    const document = {
      components: {
        schemas: {
          Article: {
            properties: {
              userId: { type: "number" },
              metadata: { properties: { createdAt: { type: "string" } } },
            },
            required: ["userId"],
            example: { userId: 1, nestedValue: [{ createdAt: "now" }] },
          },
        },
      },
      paths: {
        "/articles": {
          get: {
            parameters: [
              {
                name: "userId",
                schema: { properties: { pageSize: { type: "number" } } },
                example: { pageSize: 10 },
              },
            ],
            responses: {
              "200": {
                content: {
                  "application/json": {
                    schema: { properties: { totalCount: { type: "number" } } },
                  },
                },
              },
            },
          },
        },
      },
    } as any;

    const result = applySwaggerSnakeCase(document) as any;
    expect(result.components.schemas.Article.properties.user_id).toBeDefined();
    expect(
      result.components.schemas.Article.properties.metadata.properties
        .created_at,
    ).toBeDefined();
    expect(result.components.schemas.Article.required).toEqual(["user_id"]);
    expect(result.components.schemas.Article.example).toEqual({
      user_id: 1,
      nested_value: [{ created_at: "now" }],
    });
    expect(result.paths["/articles"].get.parameters[0].name).toBe("user_id");
    expect(
      result.paths["/articles"].get.responses["200"].content["application/json"]
        .schema.properties.total_count,
    ).toBeDefined();
  });

  // 验证该测试场景的预期行为
  it("验证该测试场景的预期行为", () => {
    const reference = { $ref: "#/components/schemas/User" };
    const document = {
      components: { schemas: { User: reference } },
      paths: {},
    } as any;
    expect(
      (applySwaggerSnakeCase(document) as any).components.schemas.User,
    ).toBe(reference);
  });
});
