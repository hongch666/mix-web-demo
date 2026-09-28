import { applyDecorators } from "@nestjs/common";
import { ApiResponse as SwaggerApiResponse } from "@nestjs/swagger";
import type { SchemaObject } from "@nestjs/swagger/dist/interfaces/open-api-spec.interface";

export interface SwaggerResponseOptions {
  data?: SchemaObject;
  description?: string;
  status?: number;
}

/** 为统一响应包装体声明可见的 data schema */
export function ApiResponseModel(
  options: SwaggerResponseOptions = {},
): MethodDecorator & ClassDecorator {
  const data: SchemaObject = options.data ?? { type: "object" };
  const responseSchema: SchemaObject = {
    type: "object",
    properties: {
      code: { type: "integer", format: "int32", example: 200 },
      msg: { type: "string", example: "success" },
      data,
    },
    required: ["code", "msg", "data"],
  };

  return applyDecorators(
    SwaggerApiResponse({
      status: options.status ?? 200,
      description: options.description ?? "成功",
      schema: responseSchema,
    }),
  );
}

/** 声明通过 Location 响应头完成跳转的 HTTP 响应。 */
export function ApiRedirectResponse(
  description = "重定向",
  status = 302,
): MethodDecorator & ClassDecorator {
  return applyDecorators(
    SwaggerApiResponse({
      status,
      description,
      headers: {
        Location: {
          description: "重定向地址",
          schema: { type: "string" },
        },
      },
    }),
  );
}

export const SwaggerNullData: SchemaObject = { type: "null", nullable: true };
export const SwaggerStringData: SchemaObject = { type: "string" };
export const SwaggerObjectData: SchemaObject = { type: "object" };
