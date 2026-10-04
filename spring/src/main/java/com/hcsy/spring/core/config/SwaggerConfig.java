package com.hcsy.spring.core.config;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.springdoc.core.customizers.OpenApiCustomizer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import com.hcsy.spring.common.constants.Defaults;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.media.ArraySchema;
import io.swagger.v3.oas.models.media.ComposedSchema;
import io.swagger.v3.oas.models.media.MapSchema;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.parameters.Parameter;
import io.swagger.v3.oas.models.servers.Server;

@Configuration
public class SwaggerConfig {

    /** 统一响应的数据字段名 */
    private static final String UNIFIED_DATA_FIELD = "data";

    /** springdoc 为泛型实参 Void 生成的 schema 名后缀，如 Result&lt;Void&gt; 对应 ResultVoid */
    private static final String VOID_SCHEMA_SUFFIX = "Void";

    /** OpenAPI 里的空数据类型：与 NestJS 的 SwaggerNullData、GoZero 的 fix.py 保持同一组声明 */
    private static final String NULL_TYPE = "null";

    private static final String OBJECT_TYPE = "object";

    @Value("${server.port}")
    private String port;

    @Bean
    OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title(Defaults.SWAGGER_TITLE)
                .version(Defaults.SWAGGER_VERSION)
                .description(Defaults.SWAGGER_DESC))
            .servers(List.of(
                new Server().url(Defaults.SWAGGER_URL_PREFIX + port).description("baseURL")));
    }

    @Bean
    OpenApiCustomizer snakeCaseOpenApiCustomizer() {
        return openApi -> {
            normalizeVoidDataSchema(openApi);
            if (openApi.getComponents() != null && openApi.getComponents().getSchemas() != null) {
                openApi.getComponents().getSchemas().values().forEach(this::transformSchema);
            }
            if (openApi.getPaths() == null) {
                return;
            }
            openApi.getPaths().values().forEach(pathItem -> pathItem.readOperations().forEach(operation -> {
                if (operation.getParameters() != null) {
                    operation.getParameters().forEach(this::transformParameter);
                }
                if (operation.getRequestBody() != null && operation.getRequestBody().getContent() != null) {
                    operation.getRequestBody().getContent().values().forEach(mediaType -> {
                        if (mediaType.getSchema() != null) {
                            transformSchema(mediaType.getSchema());
                        }
                        if (mediaType.getExample() != null) {
                            mediaType.setExample(transformExample(mediaType.getExample()));
                        }
                        if (mediaType.getExamples() != null) {
                            mediaType.getExamples().values().forEach(example -> {
                                if (example.getValue() != null) {
                                    example.setValue(transformExample(example.getValue()));
                                }
                            });
                        }
                    });
                }
                if (operation.getResponses() != null) {
                    operation.getResponses().values().forEach(apiResponse -> {
                        if (apiResponse.getContent() == null) {
                            return;
                        }
                        apiResponse.getContent().values().forEach(mediaType -> {
                            if (mediaType.getSchema() != null) {
                                transformSchema(mediaType.getSchema());
                            }
                            if (mediaType.getExample() != null) {
                                mediaType.setExample(transformExample(mediaType.getExample()));
                            }
                            if (mediaType.getExamples() != null) {
                                mediaType.getExamples().values().forEach(example -> {
                                    if (example.getValue() != null) {
                                        example.setValue(transformExample(example.getValue()));
                                    }
                                });
                            }
                        });
                    });
                }
            }));
        };
    }

    /**
     * 修正 Result&lt;Void&gt; 这类「无数据」响应的 data 声明
     *
     * springdoc 拿不到 Void 的结构信息，会把 data 写成裸 {"type":"object"}，
     * 而 Result.success() 实际返回的是 null，Apifox 与 Swagger UI 会因此展示一个空对象示例，
     * 与 NestJS、FastAPI 的空数据类型声明不一致，这里统一改写为空数据类型
     */
    private void normalizeVoidDataSchema(OpenAPI openApi) {
        if (openApi.getComponents() == null || openApi.getComponents().getSchemas() == null) {
            return;
        }
        openApi.getComponents().getSchemas().forEach((schemaName, schema) -> {
            if (schemaName == null || !schemaName.endsWith(VOID_SCHEMA_SUFFIX) || schema == null
                || schema.getProperties() == null) {
                return;
            }
            Object dataProperty = schema.getProperties().get(UNIFIED_DATA_FIELD);
            if (dataProperty instanceof Schema<?> dataSchema && isEmptyObjectSchema(dataSchema)) {
                dataSchema.setType(NULL_TYPE);
            }
        });
    }

    /** 判断是否为没有任何结构信息的裸 object：只有 type，没有 properties/additionalProperties/items/组合或引用 */
    private boolean isEmptyObjectSchema(Schema<?> schema) {
        if (!OBJECT_TYPE.equals(schema.getType())) {
            return false;
        }
        return schema.getProperties() == null && schema.getAdditionalProperties() == null
            && schema.getItems() == null && schema.getAllOf() == null && schema.getAnyOf() == null
            && schema.getOneOf() == null && schema.get$ref() == null;
    }

    private void transformParameter(Parameter parameter) {
        if (parameter == null) {
            return;
        }
        parameter.setName(toSnakeCase(parameter.getName()));
        if (parameter.getSchema() != null) {
            transformSchema(parameter.getSchema());
        }
        if (parameter.getExample() != null) {
            parameter.setExample(transformExample(parameter.getExample()));
        }
        if (parameter.getExamples() != null) {
            parameter.getExamples().values().forEach(example -> {
                if (example.getValue() != null) {
                    example.setValue(transformExample(example.getValue()));
                }
            });
        }
    }

    @SuppressWarnings({ "rawtypes", "unchecked" })
    private void transformSchema(Schema schema) {
        if (schema == null) {
            return;
        }

        if (schema.getProperties() != null && !schema.getProperties().isEmpty()) {
            Map<String, Schema> transformedProperties = new LinkedHashMap<>();
            schema.getProperties().forEach((key, value) -> {
                transformSchema((Schema) value);
                transformedProperties.put(toSnakeCase(String.valueOf(key)), (Schema) value);
            });
            schema.setProperties(transformedProperties);
        }

        if (schema.getRequired() != null && !schema.getRequired().isEmpty()) {
            List<String> transformedRequired = new ArrayList<>(schema.getRequired().size());
            schema.getRequired().forEach(item -> transformedRequired.add(toSnakeCase(String.valueOf(item))));
            schema.setRequired(transformedRequired);
        }

        if (schema.getExample() != null) {
            schema.setExample(transformExample(schema.getExample()));
        }
        if (schema.getDefault() != null) {
            schema.setDefault(transformExample(schema.getDefault()));
        }

        if (schema instanceof ArraySchema arraySchema && arraySchema.getItems() != null) {
            transformSchema(arraySchema.getItems());
        }
        if (schema instanceof MapSchema mapSchema
            && mapSchema.getAdditionalProperties() instanceof Schema additionalSchema) {
            transformSchema(additionalSchema);
        }
        if (schema instanceof ComposedSchema composedSchema) {
            transformSchemaList(composedSchema.getAllOf());
            transformSchemaList(composedSchema.getAnyOf());
            transformSchemaList(composedSchema.getOneOf());
        }
        if (schema.getNot() != null) {
            transformSchema(schema.getNot());
        }
    }

    @SuppressWarnings("rawtypes")
    private void transformSchemaList(List<Schema> schemas) {
        if (schemas == null) {
            return;
        }
        schemas.forEach(this::transformSchema);
    }

    private Object transformExample(Object value) {
        if (value instanceof Map<?, ?> mapValue) {
            Map<String, Object> transformed = new LinkedHashMap<>();
            mapValue.forEach((key, item) -> transformed.put(toSnakeCase(String.valueOf(key)), transformExample(item)));
            return transformed;
        }
        if (value instanceof List<?> listValue) {
            List<Object> transformed = new ArrayList<>(listValue.size());
            listValue.forEach(item -> transformed.add(transformExample(item)));
            return transformed;
        }
        return value;
    }

    private String toSnakeCase(String value) {
        if (value == null || value.isEmpty()) {
            return value;
        }
        return value.replaceAll("([a-z0-9])([A-Z])", "$1_$2").toLowerCase();
    }
}
