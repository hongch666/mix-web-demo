import { readFileSync } from "node:fs";
import type { INestApplication } from "@nestjs/common";
import type { OpenAPIObject } from "@nestjs/swagger";
import { DocumentBuilder, SwaggerModule } from "@nestjs/swagger";
import type { OperationObject } from "@nestjs/swagger/dist/interfaces/open-api-spec.interface";
import { SwaggerConfig } from "src/common/constants";
import { applySwaggerSnakeCase } from "src/common/utils";

/**
 * 为所有接口补全局通用错误响应（400、401、500）
 *
 * 参数校验失败、未登录/令牌失效与未捕获异常由 AllExceptionsFilter 统一转为
 * error(code, msg)，这些响应对所有接口通用，这里统一注入，避免每个控制器重复声明
 */
function applyCommonErrorResponses(document: OpenAPIObject): void {
  const schemas = document.components?.schemas;
  if (schemas) {
    schemas[SwaggerConfig.ERROR_SCHEMA_NAME] = {
      type: "object",
      description: SwaggerConfig.ERROR_SCHEMA_DESCRIPTION,
      properties: {
        code: {
          type: "integer",
          format: "int32",
          example: 400,
          description: SwaggerConfig.SCHEMA_CODE_DESCRIPTION,
        },
        msg: {
          type: "string",
          description: SwaggerConfig.SCHEMA_MSG_DESCRIPTION,
        },
        data: {
          type: "null",
          description: SwaggerConfig.SCHEMA_DATA_DESCRIPTION,
        },
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
      const responses = { ...(op.responses ?? {}) };
      const errorContent = {
        "application/json": {
          schema: {
            $ref: `#/components/schemas/${SwaggerConfig.ERROR_SCHEMA_NAME}`,
          },
        },
      };
      for (const [code, description] of SwaggerConfig.COMMON_ERROR_RESPONSES) {
        if (responses[code]) {
          continue;
        }
        responses[code] = { description, content: errorContent };
      }
      // 控制器上用 @ApiResponse 声明的业务错误码可能只写描述，
      // 统一错误体在这里补齐，避免每个接口重复声明 schema 引用
      for (const [code, response] of Object.entries(responses)) {
        if (!isErrorStatus(code)) {
          continue;
        }
        const apiResponse = response as LooseRecord | undefined;
        if (apiResponse && !("content" in apiResponse)) {
          apiResponse.content = errorContent;
        }
      }
      op.responses = responses;
    }
  }
}

/**
 * 判断响应状态码是否落在 400~599 的错误区间
 *
 * OpenAPI 的 responses 键既有数字也有 default 这类占位键，非数字一律视为非错误码
 */
function isErrorStatus(code: string): boolean {
  const value: number = Number.parseInt(code, 10);
  return Number.isInteger(value) && value >= 400 && value <= 599;
}

/** 读取网关黑名单，文件不存在时返回空数组（单独构建文档时跳过注入） */
function loadGatewayBlocklist(): string[] {
  try {
    const data = JSON.parse(
      readFileSync(SwaggerConfig.GATEWAY_BLOCKLIST_JSON, "utf-8"),
    ) as {
      uris?: string[];
    };
    return data.uris ?? [];
  } catch {
    return [];
  }
}

/** OpenAPI path 是否命中网关黑名单：精确匹配或以 * 结尾的前缀匹配 */
function isGatewayBlocked(path: string, blocklist: string[]): boolean {
  return blocklist.some((uri) =>
    uri.endsWith("*") ? path.startsWith(uri.slice(0, -1)) : path === uri,
  );
}

/**
 * 为网关 block-internal 拦截的接口补 403
 *
 * 必须在 applySwaggerSnakeCase 之后调用：网关黑名单是对外路径（下划线命名），
 * 转换前的路径可能是驼峰，先注入会漏匹配
 */
function applyGatewayInternalResponses(document: OpenAPIObject): void {
  const blocklist = loadGatewayBlocklist();
  if (blocklist.length === 0) {
    return;
  }
  for (const [path, pathItem] of Object.entries(document.paths ?? {})) {
    if (!isGatewayBlocked(path, blocklist)) {
      continue;
    }
    for (const [method, operation] of Object.entries(pathItem)) {
      if (method === "parameters") {
        continue;
      }
      const op = operation as OperationObject;
      const existing = op.responses?.["403"] as
        | { description?: string }
        | undefined;
      if (existing) {
        // 网关是外部第一道关，被拦截的接口统一用网关描述覆盖应用级 403
        existing.description = SwaggerConfig.FORBIDDEN_DESCRIPTION;
        continue;
      }
      op.responses = {
        ...(op.responses ?? {}),
        "403": {
          description: SwaggerConfig.FORBIDDEN_DESCRIPTION,
          content: {
            "application/json": {
              schema: {
                $ref: `#/components/schemas/${SwaggerConfig.ERROR_SCHEMA_NAME}`,
              },
            },
          },
        },
      };
    }
  }
}

/** 文档树上的宽松对象视图，便于按结构遍历而不逐层声明类型 */
type LooseRecord = Record<string, unknown>;

/**
 * 把路径片段或方法名转成 PascalCase 片段
 */
function toPascalName(raw: string): string {
  return raw
    .split(/[^0-9A-Za-z]+/)
    .filter((part: string) => part.length > 0)
    .map((part: string) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("");
}

/**
 * 按「服务前缀 + 路径 + 方法 + 状态码」生成响应模型名
 *
 * 用路径而不是 operationId：路径是对外契约，Apifox 也按 method+path 识别接口，
 * 重命名控制器方法不会牵动模型名。路径参数保留为 ByXxx 片段，
 * 避免 /articles 与 /articles/{id} 生成同名模型
 */
function buildModelName(
  path: string,
  method: string,
  suffix: string,
  status?: string,
): string {
  const segments: string = path
    .split("/")
    .filter((segment: string) => segment.length > 0)
    .map((segment: string) =>
      segment.startsWith("{") && segment.endsWith("}")
        ? `By${toPascalName(segment.slice(1, -1))}`
        : toPascalName(segment),
    )
    .join("");

  const statusSuffix: string =
    status === undefined || status === "200" ? "" : toPascalName(status);
  const methodSuffix: string = toPascalName(method);
  return `${SwaggerConfig.SERVICE_MODEL_PREFIX}${segments}${methodSuffix}${statusSuffix}${suffix}`;
}

/**
 * 为内联结构分配模型名：同名且内容一致时直接复用，内容不同则追加序号
 */
function reserveModelName(
  schemas: LooseRecord,
  path: string,
  method: string,
  suffix: string,
  schema: LooseRecord,
  status?: string,
): string {
  const base: string = buildModelName(path, method, suffix, status);
  const expected: string = JSON.stringify(schema);
  let name: string = base;
  let index: number = 2;
  while (name in schemas && JSON.stringify(schemas[name]) !== expected) {
    name = `${base}_${index}`;
    index += 1;
  }
  return name;
}

/**
 * 把一组 media type 下的内联 schema 提升为具名模型，原位置改为 $ref 引用
 */
function hoistMediaSchemas(
  schemas: LooseRecord,
  path: string,
  method: string,
  suffix: string,
  content: LooseRecord,
  status?: string,
): void {
  for (const [mediaType, rawMedia] of Object.entries(content)) {
    if (SwaggerConfig.NON_HOISTED_MEDIA_TYPES.has(mediaType)) {
      continue;
    }
    const media = rawMedia as LooseRecord | undefined;
    const schema = media?.schema as LooseRecord | undefined;
    if (!media || !schema) {
      continue;
    }
    if ("$ref" in schema) {
      continue;
    }
    if (
      !SwaggerConfig.STRUCTURAL_SCHEMA_KEYS.some((key: string) => key in schema)
    ) {
      continue;
    }
    const name: string = reserveModelName(
      schemas,
      path,
      method,
      suffix,
      schema,
      status,
    );
    schemas[name] = schema;
    media.schema = { $ref: `#/components/schemas/${name}` };
  }
}

/**
 * 把各接口的内联请求体与响应结构提升为 components.schemas 具名模型
 *
 * ApiResponseModel 生成的是内联 SchemaObject，同一份结构在每个接口各存一份，
 * Apifox 里既无法复用也无法按模型维度比对变更。这里在文档构建阶段统一提升：
 * 请求体除 multipart 外都提升，事件流响应整体保持内联（Apifox 靠内联帧的 title
 * 渲染流式响应），已是 $ref 的位置跳过，函数可重复执行
 */
function hoistInlineSchemas(document: OpenAPIObject): void {
  const components = (document.components ??= {});
  const schemas = (components.schemas ??= {}) as unknown as LooseRecord;

  for (const [path, rawPathItem] of Object.entries(document.paths ?? {})) {
    if (!rawPathItem) {
      continue;
    }
    for (const [method, rawOperation] of Object.entries(
      rawPathItem as unknown as LooseRecord,
    )) {
      if (!SwaggerConfig.OPERATION_METHODS.has(method)) {
        continue;
      }
      const operation = rawOperation as LooseRecord | undefined;
      if (!operation) {
        continue;
      }

      const requestContent = (operation.requestBody as LooseRecord | undefined)
        ?.content as LooseRecord | undefined;
      if (requestContent && !("multipart/form-data" in requestContent)) {
        hoistMediaSchemas(schemas, path, method, "Request", requestContent);
      }

      const responses = operation.responses as LooseRecord | undefined;
      if (!responses) {
        continue;
      }
      for (const [status, rawResponse] of Object.entries(responses)) {
        const content = (rawResponse as LooseRecord | undefined)?.content as
          | LooseRecord
          | undefined;
        if (!content) {
          continue;
        }
        // 事件流响应整体保持内联，换成 $ref 会丢掉帧节点名
        if (SwaggerConfig.STREAM_MEDIA_TYPE in content) {
          continue;
        }
        hoistMediaSchemas(schemas, path, method, "Response", content, status);
      }
    }
  }
}

/**
 * 给可空字段补上 null 类型
 *
 * OpenAPI 3.1 用类型数组表达可空（如 ["string","null"]），而 @ApiProperty({ nullable: true })
 * 在 3.1 产物里不会体现。这里按 required 判定：未列入 required 的属性（@ApiProperty 声明了
 * required: false）视为可空，统一补 null；要声明「不允许为 null」就保持 required 默认的 true。
 * 不补的表现是 Apifox「校验响应」把合法的 null 判成「$.data.xxx 不允许为 null」
 */
function markNullableProperties(document: OpenAPIObject): void {
  const schemas = document.components?.schemas as LooseRecord | undefined;
  if (schemas) {
    Object.values(schemas).forEach((schema) =>
      markSchemaNullable(schema as LooseRecord),
    );
  }

  for (const rawPathItem of Object.values(document.paths ?? {})) {
    for (const [method, rawOperation] of Object.entries(
      rawPathItem as unknown as LooseRecord,
    )) {
      if (!SwaggerConfig.OPERATION_METHODS.has(method)) {
        continue;
      }
      const operation = rawOperation as LooseRecord | undefined;
      if (!operation) {
        continue;
      }
      const requestContent = (operation.requestBody as LooseRecord | undefined)
        ?.content as LooseRecord | undefined;
      if (requestContent) {
        Object.values(requestContent).forEach((media) =>
          markSchemaNullable(
            (media as LooseRecord | undefined)?.schema as
              | LooseRecord
              | undefined,
          ),
        );
      }
      const responses = operation.responses as LooseRecord | undefined;
      if (!responses) {
        continue;
      }
      Object.values(responses).forEach((rawResponse) => {
        const content = (rawResponse as LooseRecord | undefined)?.content as
          | LooseRecord
          | undefined;
        if (!content) {
          return;
        }
        Object.values(content).forEach((media) =>
          markSchemaNullable(
            (media as LooseRecord | undefined)?.schema as
              | LooseRecord
              | undefined,
          ),
        );
      });
    }
  }
}

/** 递归标记 schema 里未列入 required 的属性为可空，并继续下钻 items / 组合结构 */
function markSchemaNullable(schema: LooseRecord | undefined): void {
  if (!schema) {
    return;
  }
  const properties = schema.properties as LooseRecord | undefined;
  if (properties) {
    const required = Array.isArray(schema.required)
      ? (schema.required as string[])
      : [];
    for (const [name, rawProperty] of Object.entries(properties)) {
      if (!required.includes(name)) {
        markPropertyNullable(rawProperty as LooseRecord);
      }
    }
  }

  const items = schema.items as LooseRecord | undefined;
  if (items) {
    markSchemaNullable(items);
  }

  const additional = schema.additionalProperties as LooseRecord | undefined;
  if (additional && typeof additional === "object") {
    markSchemaNullable(additional);
  }

  for (const key of ["allOf", "anyOf", "oneOf"] as const) {
    const branches = schema[key];
    if (Array.isArray(branches)) {
      branches.forEach((branch) => markSchemaNullable(branch as LooseRecord));
    }
  }
}

/**
 * 给单个属性补 null 类型
 *
 * $ref 属性无法在 3.1 里直接扩展、带 enum 的属性补 null 会产生「类型允许 null 但取值不允许」的
 * 自相矛盾 schema，两种情况都保持原样
 */
function markPropertyNullable(property: LooseRecord | undefined): void {
  if (!property || "$ref" in property || "enum" in property) {
    return;
  }
  const type = property.type;
  if (Array.isArray(type)) {
    if (!type.includes(SwaggerConfig.NULL_TYPE)) {
      type.push(SwaggerConfig.NULL_TYPE);
    }
    return;
  }
  if (typeof type !== "string" || type === SwaggerConfig.NULL_TYPE) {
    return;
  }
  property.type = [type, SwaggerConfig.NULL_TYPE];
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

  applyCommonErrorResponses(document);

  hoistInlineSchemas(document);

  const named: OpenAPIObject = applySwaggerSnakeCase(document);

  applyGatewayInternalResponses(named);

  markNullableProperties(named);

  return named;
}
