import type {
  OpenAPIObject,
  OperationObject,
  ParameterObject,
  ReferenceObject,
  SchemaObject,
} from '@nestjs/swagger/dist/interfaces/open-api-spec.interface';

function isReferenceObject(value: unknown): value is ReferenceObject {
  return (
    typeof value === 'object' &&
    value !== null &&
    '$ref' in value &&
    typeof (value as { $ref?: unknown }).$ref === 'string'
  );
}

function isSchemaObject(value: unknown): value is SchemaObject {
  return typeof value === 'object' && value !== null && !isReferenceObject(value);
}

function toSnakeCase(key: string): string {
  return key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
}

function transformExample<T>(value: T): T {
  if (Array.isArray(value)) {
    return value.map((item) => transformExample(item)) as T;
  }

  if (value === null || typeof value !== 'object') {
    return value;
  }

  const result: Record<string, unknown> = {};
  Object.entries(value as Record<string, unknown>).forEach(([key, item]) => {
    result[toSnakeCase(key)] = transformExample(item);
  });
  return result as T;
}

function transformSchema(schema?: SchemaObject | ReferenceObject): void {
  if (!schema || isReferenceObject(schema)) {
    return;
  }

  if (schema.properties) {
    const transformedProperties: Record<string, SchemaObject | ReferenceObject> = {};
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

  if (schema.additionalProperties && isSchemaObject(schema.additionalProperties)) {
    transformSchema(schema.additionalProperties);
  }

  schema.allOf?.forEach((item) => transformSchema(item));
  schema.anyOf?.forEach((item) => transformSchema(item));
  schema.oneOf?.forEach((item) => transformSchema(item));

  if (schema.not && isSchemaObject(schema.not)) {
    transformSchema(schema.not);
  }
}

function transformParameter(parameter: ParameterObject | ReferenceObject): void {
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
      if (typeof example === 'object' && example !== null && 'value' in example) {
        example.value = transformExample(example.value);
      }
    });
  }
}

function transformOperation(operation: OperationObject): void {
  operation.parameters?.forEach((parameter) => transformParameter(parameter));

  if (operation.requestBody && !isReferenceObject(operation.requestBody)) {
    Object.values(operation.requestBody.content ?? {}).forEach((mediaType) => {
      transformSchema(mediaType.schema);
      if (mediaType.example !== undefined) {
        mediaType.example = transformExample(mediaType.example);
      }
      Object.values(mediaType.examples ?? {}).forEach((example) => {
        if (typeof example === 'object' && example !== null && 'value' in example) {
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
        if (typeof example === 'object' && example !== null && 'value' in example) {
          example.value = transformExample(example.value);
        }
      });
    });
  });
}

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
