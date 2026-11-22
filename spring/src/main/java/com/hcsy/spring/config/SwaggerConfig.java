package com.hcsy.spring.config;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.springdoc.core.customizers.OpenApiCustomizer;
import org.springdoc.core.customizers.OperationCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.AnnotatedElementUtils;
import org.springframework.core.annotation.AnnotationUtils;
import org.springframework.web.method.HandlerMethod;

import com.hcsy.spring.common.constants.Defaults;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.config.properties.ServerProperties;
import com.hcsy.spring.web.security.annotation.RequirePermission;
import com.hcsy.spring.web.swagger.annotation.ApiErrorCode;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.media.ArraySchema;
import io.swagger.v3.oas.models.media.ComposedSchema;
import io.swagger.v3.oas.models.media.Content;
import io.swagger.v3.oas.models.media.MapSchema;
import io.swagger.v3.oas.models.media.MediaType;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.parameters.Parameter;
import io.swagger.v3.oas.models.responses.ApiResponse;
import io.swagger.v3.oas.models.responses.ApiResponses;
import io.swagger.v3.oas.models.servers.Server;
import lombok.RequiredArgsConstructor;

/**
 * 装配 OpenAPI 文档信息，并统一定制下划线命名、空数据声明与 401 错误响应
 */
@Configuration
@RequiredArgsConstructor
public class SwaggerConfig {

    private final ServerProperties serverProperties;

    /** 统一响应的数据字段名 */
    private static final String UNIFIED_DATA_FIELD = "data";

    /** springdoc 为泛型实参 Void 生成的 schema 名后缀，如 Result&lt;Void&gt; 对应 ResultVoid */
    private static final String VOID_SCHEMA_SUFFIX = "Void";

    /** OpenAPI 里的空数据类型：与 NestJS 的 SwaggerNullData、GoZero 的 fix.py 保持同一组声明 */
    private static final String NULL_TYPE = "null";

    private static final String OBJECT_TYPE = "object";

    /** 统一错误响应的 schema 名，注册在 components 下供各接口引用 */
    private static final String ERROR_SCHEMA_NAME = "ErrorResponse";

    /** 错误响应的 JSON 媒体类型 */
    private static final String JSON_MEDIA_TYPE = "application/json";

    @Bean
    OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title(Defaults.SWAGGER_TITLE)
                .version(Defaults.SWAGGER_VERSION)
                .description(Defaults.SWAGGER_DESC))
            .servers(List.of(
                new Server().url(Defaults.SWAGGER_URL_PREFIX + serverProperties.port()).description("baseURL")));
    }

    /**
     * 按接口声明补业务错误响应
     *
     * @ApiErrorCode 标注业务错误码（如 404/409/422），@RequirePermission 隐含 403，
     * 两者都在 springdoc 生成 operation 之后注入，不影响自动生成的 200 成功响应
     */
    @Bean
    OperationCustomizer errorResponseCustomizer() {
        return (operation, handlerMethod) -> {
            if (operation.getResponses() == null) {
                operation.setResponses(new ApiResponses());
            }
            collectApiErrorCodes(handlerMethod).forEach(annotation -> addErrorResponse(operation,
                annotation.code(), annotation.description()));
            if (requiresPermission(handlerMethod)) {
                addErrorResponse(operation, "403", Messages.FORBIDDEN_DESCRIPTION);
            }
            return operation;
        };
    }

    /**
     * 定制 OpenAPI 文档，将 schema、参数与示例统一转为下划线命名并补充通用错误响应
     */
    @Bean
    OpenApiCustomizer snakeCaseOpenApiCustomizer() {
        return openApi -> {
            normalizeVoidDataSchema(openApi);
            addGatewayInternalResponses(openApi);
            addCommonErrorResponses(openApi);
            if (openApi.getComponents() != null && openApi.getComponents().getSchemas() != null) {
                openApi.getComponents().getSchemas().values().forEach(this::transformSchema);
            }
            if (openApi.getPaths() == null) {
                markNullableProperties(openApi);
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
            markNullableProperties(openApi);
        };
    }

    /**
     * 为可为 null 的字段补上 null 类型
     *
     * OpenAPI 3.1 用 type 数组表达可空（如 ["string","null"]），而 @Schema(nullable = true) 是 3.0 的写法，
     * springdoc 以 openapi_3_1 输出时直接忽略它。Java 的引用类型本身就可能为 null，DB 可空列取出来也是 null，
     * 因此对未列入 required 的属性统一补 null：需要声明「不允许为 null」时，在字段上打 @NotNull / @NotBlank /
     * @NotEmpty 或 @Schema(requiredMode = REQUIRED)，springdoc 会把它写进 required，这里就不再补 null。
     * 不补的表现是 Apifox「校验响应」把合法的 null 判成「$.data.github_id 不允许为 null」
     */
    private void markNullableProperties(OpenAPI openApi) {
        if (openApi.getComponents() != null && openApi.getComponents().getSchemas() != null) {
            openApi.getComponents().getSchemas().values().forEach(this::markSchemaNullable);
        }
        if (openApi.getPaths() == null) {
            return;
        }
        openApi.getPaths().values().forEach(pathItem -> pathItem.readOperations().forEach(operation -> {
            if (operation.getRequestBody() != null && operation.getRequestBody().getContent() != null) {
                operation.getRequestBody().getContent().values()
                    .forEach(mediaType -> markSchemaNullable(mediaType.getSchema()));
            }
            if (operation.getResponses() == null) {
                return;
            }
            operation.getResponses().values().forEach(apiResponse -> {
                if (apiResponse.getContent() == null) {
                    return;
                }
                apiResponse.getContent().values().forEach(mediaType -> markSchemaNullable(mediaType.getSchema()));
            });
        }));
    }

    /** 递归标记 schema 里未列入 required 的属性为可空 */
    private void markSchemaNullable(Schema<?> schema) {
        if (schema == null) {
            return;
        }
        if (schema.getProperties() != null) {
            List<String> required = schema.getRequired() == null ? List.of() : schema.getRequired();
            schema.getProperties().forEach((name, value) -> {
                if (value instanceof Schema<?> property && !required.contains(String.valueOf(name))) {
                    markPropertyNullable(property);
                }
            });
        }
        if (schema instanceof ArraySchema arraySchema) {
            markSchemaNullable(arraySchema.getItems());
        }
        if (schema instanceof MapSchema mapSchema
            && mapSchema.getAdditionalProperties() instanceof Schema additionalSchema) {
            markSchemaNullable(additionalSchema);
        }
        if (schema instanceof ComposedSchema composedSchema) {
            transformSchemaListNullable(composedSchema.getAllOf());
            transformSchemaListNullable(composedSchema.getAnyOf());
            transformSchemaListNullable(composedSchema.getOneOf());
        }
    }

    /** 给单个属性补 null 类型；$ref 属性无法在 3.1 里直接扩展，保持原样 */
    private void markPropertyNullable(Schema<?> property) {
        if (property == null || property.get$ref() != null) {
            return;
        }
        if (property.getTypes() == null || property.getTypes().isEmpty()) {
            if (property.getType() == null) {
                return;
            }
            property.addType(property.getType());
        }
        if (!property.getTypes().contains(NULL_TYPE)) {
            property.addType(NULL_TYPE);
        }
    }

    @SuppressWarnings("rawtypes")
    private void transformSchemaListNullable(List<Schema> schemas) {
        if (schemas == null) {
            return;
        }
        schemas.forEach(this::markSchemaNullable);
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

    /**
     * 为所有接口补全局通用错误响应（400、401、500）
     *
     * 参数校验失败、未登录/令牌失效与未捕获异常分别由 GlobalExceptionHandler 统一转为
     * Result.error(code, msg)，这三类响应对所有接口通用，但 springdoc 只能收集单个接口
     * 显式声明的错误响应，这里统一注入，避免每个控制器重复声明
     */
    private void addCommonErrorResponses(OpenAPI openApi) {
        if (openApi.getPaths() == null) {
            return;
        }
        registerErrorSchema(openApi);
        Map<String, String> commonResponses = new LinkedHashMap<>();
        commonResponses.put("400", Messages.BAD_REQUEST_DESCRIPTION);
        commonResponses.put("401", Messages.USER_NOT_LOGIN);
        commonResponses.put("500", Messages.INTERNAL_SERVER_ERROR_DESCRIPTION);
        openApi.getPaths().values().forEach(pathItem -> pathItem.readOperations().forEach(operation -> {
            if (operation.getResponses() == null) {
                operation.setResponses(new ApiResponses());
            }
            commonResponses.forEach((code, description) -> {
                if (!operation.getResponses().containsKey(code)) {
                    operation.getResponses().addApiResponse(code, new ApiResponse()
                        .description(description)
                        .content(errorContent()));
                }
            });
            // 接口上用 @ApiResponse 声明的业务错误码（如 404/409/422）只写描述，
            // 统一错误体在这里补齐，避免每个控制器重复写 schema 引用
            operation.getResponses().forEach((code, response) -> {
                if (response.getContent() == null && isErrorStatus(code)) {
                    response.setContent(errorContent());
                }
            });
        }));
    }

    /** 统一错误响应体：引用 components 下的 ErrorResponse */
    private Content errorContent() {
        return new Content().addMediaType(JSON_MEDIA_TYPE, new MediaType()
            .schema(new Schema<>().$ref("#/components/schemas/" + ERROR_SCHEMA_NAME)));
    }

    /**
     * 为网关 block-internal 拦截的接口补 403
     *
     * 网关按 URI 黑名单拦截，服务代码无法推导，只能从 scripts/generated 下的共享 JSON 读取；
     * 这里只补描述，统一错误体由 addCommonErrorResponses 补齐
     */
    private void addGatewayInternalResponses(OpenAPI openApi) {
        if (openApi.getPaths() == null) {
            return;
        }
        List<String> blocklist = loadGatewayBlocklist();
        if (blocklist.isEmpty()) {
            return;
        }
        openApi.getPaths().forEach((path, pathItem) -> {
            if (!isGatewayBlocked(path, blocklist)) {
                return;
            }
            pathItem.readOperations().forEach(operation -> {
                if (operation.getResponses() == null) {
                    operation.setResponses(new ApiResponses());
                }
                ApiResponse forbidden = operation.getResponses().get("403");
                if (forbidden == null) {
                    operation.getResponses().addApiResponse("403", new ApiResponse()
                        .description(Messages.GATEWAY_FORBIDDEN_DESCRIPTION)
                        .content(errorContent()));
                } else {
                    // 网关是外部第一道关，被拦截的接口统一用网关描述覆盖 @RequirePermission 等应用级 403
                    forbidden.setDescription(Messages.GATEWAY_FORBIDDEN_DESCRIPTION);
                }
            });
        });
    }

    /** 读取共享的网关黑名单 JSON，文件不存在时返回空列表 */
    private List<String> loadGatewayBlocklist() {
        for (Path candidate : gatewayBlocklistCandidates()) {
            if (!Files.isRegularFile(candidate)) {
                continue;
            }
            try {
                JsonNode root = new ObjectMapper().readTree(candidate.toFile());
                List<String> uris = new ArrayList<>();
                root.path("uris").forEach(uri -> uris.add(uri.asText()));
                return uris;
            } catch (IOException ignored) {
                return List.of();
            }
        }
        return List.of();
    }

    /** 黑名单 JSON 候选路径：环境变量（swag-init.sh 注入）优先，再试常见工作目录 */
    private List<Path> gatewayBlocklistCandidates() {
        List<Path> candidates = new ArrayList<>();
        String configured = System.getenv("GATEWAY_BLOCKLIST_JSON");
        if (configured != null && !configured.isBlank()) {
            candidates.add(Path.of(configured));
        }
        candidates.add(Path.of("scripts/generated/gateway-blocklist.json"));
        candidates.add(Path.of("../scripts/generated/gateway-blocklist.json"));
        return candidates;
    }

    /** OpenAPI path 是否命中网关黑名单：精确匹配或以 * 结尾的前缀匹配 */
    private boolean isGatewayBlocked(String path, List<String> blocklist) {
        return blocklist.stream().anyMatch(uri -> uri.endsWith("*")
            ? path.startsWith(uri.substring(0, uri.length() - 1))
            : path.equals(uri));
    }

    /** 收集接口方法与其控制器类上声明的业务错误码 */
    private List<ApiErrorCode> collectApiErrorCodes(HandlerMethod handlerMethod) {
        List<ApiErrorCode> codes = new ArrayList<>();
        // 单个 @ApiErrorCode 不会生成容器注解，必须用 getRepeatableAnnotations 才能同时覆盖单次与重复声明
        codes.addAll(AnnotationUtils.getRepeatableAnnotations(handlerMethod.getMethod(), ApiErrorCode.class));
        codes.addAll(AnnotationUtils.getRepeatableAnnotations(handlerMethod.getBeanType(), ApiErrorCode.class));
        return codes;
    }

    /** 向 operation 追加错误响应，已声明过的状态码保持原样 */
    private void addErrorResponse(Operation operation, String code, String description) {
        if (operation.getResponses().containsKey(code)) {
            return;
        }
        operation.getResponses().addApiResponse(code, new ApiResponse()
            .description(description)
            .content(errorContent()));
    }

    /** 判断接口方法或其控制器类是否声明了 @RequirePermission */
    private boolean requiresPermission(HandlerMethod handlerMethod) {
        return AnnotatedElementUtils.hasAnnotation(handlerMethod.getMethod(), RequirePermission.class)
            || AnnotatedElementUtils.hasAnnotation(handlerMethod.getBeanType(), RequirePermission.class);
    }

    /** 判断状态码字符串是否落在 4xx/5xx 区间，非数字状态码（如 default）返回 false */
    private boolean isErrorStatus(String code) {
        if (code == null) {
            return false;
        }
        try {
            int value = Integer.parseInt(code);
            return value >= 400 && value <= 599;
        } catch (NumberFormatException ex) {
            return false;
        }
    }

    /** 注册统一错误响应的 schema，结构与 Result.error(code, msg) 的实际输出一致 */
    @SuppressWarnings({ "rawtypes" })
    private void registerErrorSchema(OpenAPI openApi) {
        if (openApi.getComponents() == null || openApi.getComponents().getSchemas() == null) {
            return;
        }
        Map<String, Schema> schemas = openApi.getComponents().getSchemas();
        if (schemas.containsKey(ERROR_SCHEMA_NAME)) {
            return;
        }
        Map<String, Schema> properties = new LinkedHashMap<>();
        Schema codeSchema = typedSchema("integer", Messages.SCHEMA_RESPONSE_CODE);
        codeSchema.setFormat("int32");
        codeSchema.setExample(400);
        properties.put("code", codeSchema);
        properties.put("msg", typedSchema("string", Messages.SCHEMA_RESPONSE_MESSAGE));
        properties.put("data", typedSchema(NULL_TYPE, Messages.SCHEMA_RESPONSE_DATA));

        Schema schema = typedSchema(OBJECT_TYPE, Messages.SCHEMA_ERROR_RESPONSE);
        schema.setProperties(properties);
        schema.setRequired(List.of("code", "msg", "data"));
        schemas.put(ERROR_SCHEMA_NAME, schema);
    }

    /**
     * 构造声明了类型的 schema
     *
     * swagger-models 的 type 与 types 分别标注 @OpenAPI30 与 @OpenAPI31，
     * springdoc 以 openapi_3_1 输出时只认 types 集合，两个字段必须同时写入
     */
    @SuppressWarnings({ "rawtypes" })
    private Schema typedSchema(String type, String description) {
        Schema schema = new Schema();
        schema.setType(type);
        schema.addType(type);
        schema.setDescription(description);
        return schema;
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

    /**
     * 将接口参数名称、schema 与示例转换为下划线命名
     */
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

    /**
     * 递归将 schema 的属性、必填项与默认值转换为下划线命名
     */
    @SuppressWarnings({ "rawtypes" })
    private void transformSchema(Schema<?> schema) {
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

    /**
     * 批量转换 allOf/anyOf/oneOf 组合 schema 列表
     */
    @SuppressWarnings("rawtypes")
    private void transformSchemaList(List<Schema> schemas) {
        if (schemas == null) {
            return;
        }
        schemas.forEach(this::transformSchema);
    }

    /**
     * 递归将示例值中 Map 的键转换为下划线命名
     */
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

    /**
     * 将驼峰命名转换为下划线命名
     */
    private String toSnakeCase(String value) {
        if (value == null || value.isEmpty()) {
            return value;
        }
        return value.replaceAll("([a-z0-9])([A-Z])", "$1_$2").toLowerCase();
    }
}
