import type {
  OpenAPIObject,
  OperationObject,
  ParameterObject,
  ReferenceObject,
  SchemaObject,
} from "@nestjs/swagger/dist/interfaces/open-api-spec.interface";
import { toSnakeCase } from "src/common/utils/snakeCase";

/**
 * 判断值是否为 OpenAPI 的 $ref 引用对象
 */
function isReferenceObject(value: unknown): value is ReferenceObject {
  return (
    typeof value === "object" &&
    value !== null &&
    "$ref" in value &&
    typeof (value as { $ref?: unknown }).$ref === "string"
  );
}

/**
 * 判断值是否为普通 SchemaObject（非 $ref 引用），供转换前的类型收窄使用
 */
function isSchemaObject(value: unknown): value is SchemaObject {
  return (
    typeof value === "object" && value !== null && !isReferenceObject(value)
  );
}

/**
 * 递归转换 example/default 示例数据中的对象键为下划线命名，保持 Swagger 示例与实际响应字段一致
 */
function transformExample<T>(value: T): T {
  if (Array.isArray(value)) {
    return value.map((item) => transformExample(item)) as T;
  }

  if (value === null || typeof value !== "object") {
    return value;
  }

  const result: Record<string, unknown> = {};
  Object.entries(value as Record<string, unknown>).forEach(([key, item]) => {
    result[toSnakeCase(key)] = transformExample(item);
  });
  return result as T;
}

/**
 * 递归转换 schema 内 properties 键名、required 字段列表及嵌套 schema 的 example/default 为下划线命名
 */
function transformSchema(schema?: SchemaObject | ReferenceObject): void {
  if (!schema || isReferenceObject(schema)) {
    return;
  }

  if (schema.properties) {
    const transformedProperties: Record<
      string,
      SchemaObject | ReferenceObject
    > = {};
    Object.entries(schema.properties).forEach(([key, value]) => {
      transformSchema(value);
      transformedProperties[toSnakeCase(key)] = value;
    });
    schema.properties = transformedProperties;
  }

  if (schema.required) {
    schema.required = schema.required.map((item) => toSnakeCase(item));
  }

  if (schema.example !== undefined) {
    schema.example = transformExample(schema.example);
  }

  if (schema.default !== undefined) {
    schema.default = transformExample(schema.default);
  }

  if (schema.items && isSchemaObject(schema.items)) {
    transformSchema(schema.items);
  }

  if (
    schema.additionalProperties &&
    isSchemaObject(schema.additionalProperties)
  ) {
    transformSchema(schema.additionalProperties);
  }

  schema.allOf?.forEach((item) => transformSchema(item));
  schema.anyOf?.forEach((item) => transformSchema(item));
  schema.oneOf?.forEach((item) => transformSchema(item));

  if (schema.not && isSchemaObject(schema.not)) {
    transformSchema(schema.not);
  }
}

/**
 * 转换 OpenAPI 参数定义，将参数名及其 schema、示例中的键名统一为下划线命名
 */
function transformParameter(
  parameter: ParameterObject | ReferenceObject,
): void {
  if (isReferenceObject(parameter)) {
    return;
  }

  parameter.name = toSnakeCase(parameter.name);

  if (parameter.schema && isSchemaObject(parameter.schema)) {
    transformSchema(parameter.schema);
  }

  if (parameter.example !== undefined) {
    parameter.example = transformExample(parameter.example);
  }

  if (parameter.examples) {
    Object.values(parameter.examples).forEach((example) => {
      if (
        typeof example === "object" &&
        example !== null &&
        "value" in example
      ) {
        example.value = transformExample(example.value);
      }
    });
  }
}

/**
 * 转换单个 OpenAPI 操作的参数、请求体与各响应体的 schema 及示例键名为下划线命名
 */
function transformOperation(operation: OperationObject): void {
  operation.parameters?.forEach((parameter) => transformParameter(parameter));

  if (operation.requestBody && !isReferenceObject(operation.requestBody)) {
    Object.values(operation.requestBody.content ?? {}).forEach((mediaType) => {
      transformSchema(mediaType.schema);
      if (mediaType.example !== undefined) {
        mediaType.example = transformExample(mediaType.example);
      }
      Object.values(mediaType.examples ?? {}).forEach((example) => {
        if (
          typeof example === "object" &&
          example !== null &&
          "value" in example
        ) {
          example.value = transformExample(example.value);
        }
      });
    });
  }

  Object.values(operation.responses ?? {}).forEach((response) => {
    if (!response || isReferenceObject(response)) {
      return;
    }
    Object.values(response.content ?? {}).forEach((mediaType) => {
      transformSchema(mediaType.schema);
      if (mediaType.example !== undefined) {
        mediaType.example = transformExample(mediaType.example);
      }
      Object.values(mediaType.examples ?? {}).forEach((example) => {
        if (
          typeof example === "object" &&
          example !== null &&
          "value" in example
        ) {
          example.value = transformExample(example.value);
        }
      });
    });
  });
}

/**
 * 遍历整个 Swagger 文档的 components 与所有 paths 操作，将全部字段命名统一为下划线风格以匹配对外接口契约
 */
export function applySwaggerSnakeCase(document: OpenAPIObject): OpenAPIObject {
  Object.values(document.components?.schemas ?? {}).forEach((schema) => {
    transformSchema(schema);
  });

  Object.values(document.paths ?? {}).forEach((pathItem) => {
    if (!pathItem) {
      return;
    }
    [
      pathItem.get,
      pathItem.put,
      pathItem.post,
      pathItem.delete,
      pathItem.options,
      pathItem.head,
      pathItem.patch,
      pathItem.trace,
    ]
      .filter((operation): operation is OperationObject => Boolean(operation))
      .forEach((operation) => transformOperation(operation));
  });

  return document;
}
