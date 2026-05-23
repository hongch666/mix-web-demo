package com.hcsy.spring.core.config;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.springdoc.core.customizers.OpenApiCustomizer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import com.hcsy.spring.common.utils.Constants;

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

    @Value("${server.port}")
    private String port;

    @Bean
    OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title(Constants.SWAGGER_TITLE)
                .version(Constants.SWAGGER_VERSION)
                .description(Constants.SWAGGER_DESC))
            .servers(List.of(
                new Server().url(Constants.SWAGGER_URL_PREFIX + port).description("baseURL")));
    }

    @Bean
    OpenApiCustomizer snakeCaseOpenApiCustomizer() {
        return openApi -> {
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
        if (schema instanceof MapSchema mapSchema && mapSchema.getAdditionalProperties() instanceof Schema additionalSchema) {
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
