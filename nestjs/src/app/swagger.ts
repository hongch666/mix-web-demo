import type { INestApplication } from "@nestjs/common";
import type { OpenAPIObject } from "@nestjs/swagger";
import type { OperationObject } from "@nestjs/swagger/dist/interfaces/open-api-spec.interface";
import { DocumentBuilder, SwaggerModule } from "@nestjs/swagger";
import { SwaggerConfig } from "src/common/constants";
import { applySwaggerSnakeCase } from "src/common/utils/swaggerSnakeCase";

/** 401 统一错误响应的描述文案 */
const UNAUTHORIZED_DESCRIPTION = "用户未登录或登录已失效";

/** 401 统一错误响应的 schema 名 */
const UNAUTHORIZED_SCHEMA_NAME = "UnauthorizedResponse";

/**
 * 为所有接口补统一的 401 未登录响应
 *
 * 未登录或令牌失效由 AllExceptionsFilter 统一转为 error(401, msg)，
 * 该响应对所有接口通用，这里统一注入，避免每个控制器重复声明
 */
function applyCommonUnauthorizedResponses(document: OpenAPIObject): void {
  const schemas = document.components?.schemas;
  if (schemas) {
    schemas[UNAUTHORIZED_SCHEMA_NAME] = {
      type: "object",
      description: "统一错误响应",
      properties: {
        code: {
          type: "integer",
          format: "int32",
          example: 401,
          description: "响应码，与 HTTP 状态码一致",
        },
        msg: { type: "string", description: "响应消息" },
        data: { type: "null", description: "返回数据" },
      },
      required: ["code", "msg", "data"],
    };
  }

  for (const pathItem of Object.values(document.paths ?? {})) {
    for (const [method, operation] of Object.entries(pathItem)) {
      if (method === "parameters") {
        continue;
      }
      const op = operation as OperationObject;
      if (op.responses?.["401"]) {
        continue;
      }
      op.responses = {
        ...(op.responses ?? {}),
        "401": {
          description: UNAUTHORIZED_DESCRIPTION,
          content: {
            "application/json": {
              schema: {
                $ref: `#/components/schemas/${UNAUTHORIZED_SCHEMA_NAME}`,
              },
            },
          },
        },
      };
    }
  }
}

/**
 * 构建 Swagger/OpenAPI 文档对象
 *
 * 运行时（app/index.ts）与离线生成脚本（script/generateOpenapi.ts）共用同一份构建逻辑，
 * 避免两处配置漂移
 */
export function buildSwaggerDocument(app: INestApplication): OpenAPIObject {
  const swaggerBuilder = new DocumentBuilder()
    .setTitle(SwaggerConfig.SWAGGER_TITLE)
    .setDescription(SwaggerConfig.SWAGGER_DESCRIPTION)
    .setVersion(SwaggerConfig.SWAGGER_VERSION)
    .setOpenAPIVersion(SwaggerConfig.OPENAPI_VERSION);

  SwaggerConfig.SWAGGER_TAGS.forEach(([name, description]) => {
    swaggerBuilder.addTag(name, description);
  });

  const config: Omit<OpenAPIObject, "paths"> = swaggerBuilder.build();
  const document: OpenAPIObject = SwaggerModule.createDocument(app, config);
  applyCommonUnauthorizedResponses(document);
  return applySwaggerSnakeCase(document);
}
