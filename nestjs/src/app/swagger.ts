import type { INestApplication } from "@nestjs/common";
import type { OpenAPIObject } from "@nestjs/swagger";
import { DocumentBuilder, SwaggerModule } from "@nestjs/swagger";
import type { OperationObject } from "@nestjs/swagger/dist/interfaces/open-api-spec.interface";
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

/** 提升为具名响应模型时加的服务前缀，避免与其他服务在同名路径上互相覆盖模型 */
const SERVICE_MODEL_PREFIX = "Nestjs";

/** 参与模型提升的 HTTP 方法 */
const OPERATION_METHODS: ReadonlySet<string> = new Set([
  "get",
  "post",
  "put",
  "delete",
  "patch",
  "head",
  "options",
  "trace",
]);

/** 只有带结构信息的内联 schema 才提升为具名模型，裸 object 与标量提升后只是噪音 */
const STRUCTURAL_SCHEMA_KEYS: readonly string[] = [
  "properties",
  "items",
  "allOf",
  "anyOf",
  "oneOf",
  "enum",
];

/** SSE 帧必须保持内联：Apifox 依赖内联的帧 schema 渲染 text/event-stream 响应 */
const NON_HOISTED_MEDIA_TYPES: ReadonlySet<string> = new Set([
  "text/event-stream",
]);

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
  return `${SERVICE_MODEL_PREFIX}${segments}${methodSuffix}${statusSuffix}${suffix}`;
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
    if (NON_HOISTED_MEDIA_TYPES.has(mediaType)) {
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
    if (!STRUCTURAL_SCHEMA_KEYS.some((key: string) => key in schema)) {
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
      if (!OPERATION_METHODS.has(method)) {
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
        if ("text/event-stream" in content) {
          continue;
        }
        hoistMediaSchemas(schemas, path, method, "Response", content, status);
      }
    }
  }
}

/** OpenAPI 3.1 里表示「允许为 null」的类型标记 */
const NULL_TYPE = "null";

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
      if (!OPERATION_METHODS.has(method)) {
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
    if (!type.includes(NULL_TYPE)) {
      type.push(NULL_TYPE);
    }
    return;
  }
  if (typeof type !== "string" || type === NULL_TYPE) {
    return;
  }
  property.type = [type, NULL_TYPE];
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
  // 先提升再统一命名：提升后的模型内容与接口响应共用同一份结构，避免两处转换不一致
  hoistInlineSchemas(document);
  const named: OpenAPIObject = applySwaggerSnakeCase(document);
  // 命名统一之后再补可空类型：required 与 properties 的键此时都是下划线命名，比较才对得上
  markNullableProperties(named);
  return named;
}
