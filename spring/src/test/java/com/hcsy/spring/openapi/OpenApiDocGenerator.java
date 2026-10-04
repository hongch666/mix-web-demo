package com.hcsy.spring.openapi;

import java.lang.reflect.Constructor;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashSet;
import java.util.Set;

import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springdoc.core.configuration.SpringDocConfiguration;
import org.springdoc.core.configuration.SpringDocSpecPropertiesConfiguration;
import org.springdoc.core.properties.SpringDocConfigProperties;
import org.springdoc.webflux.core.configuration.SpringDocWebFluxConfiguration;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.config.BeanFactoryPostProcessor;
import org.springframework.beans.factory.config.ConfigurableListableBeanFactory;
import org.springframework.beans.factory.support.BeanDefinitionRegistry;
import org.springframework.beans.factory.support.RootBeanDefinition;
import org.springframework.boot.test.autoconfigure.web.reactive.AutoConfigureWebTestClient;
import org.springframework.boot.test.autoconfigure.web.reactive.WebFluxTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ClassPathScanningCandidateComponentProvider;
import org.springframework.context.annotation.Import;
import org.springframework.core.type.filter.AnnotationTypeFilter;
import org.springframework.stereotype.Controller;
import org.springframework.test.web.reactive.server.WebTestClient;
import org.springframework.web.bind.annotation.ControllerAdvice;

import com.hcsy.spring.core.config.SwaggerConfig;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.util.DefaultIndenter;
import com.fasterxml.jackson.core.util.DefaultPrettyPrinter;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.dataformat.yaml.YAMLMapper;

/**
 * Spring 侧 OpenAPI 静态产物生成器（离线、不依赖 Redis/Nacos/MySQL 等任何中间件）
 *
 * 实现思路：只装配 Web 层（Controller、ControllerAdvice、WebFilter）与 springdoc，
 * 控制器与通知类依赖的所有业务/基础设施 bean 由 Mockito 自动补齐，
 * 因此无需启动完整应用、无需读取 .env、也不占用任何端口
 *
 * 产物默认写入 Spring 模块自身的 docs/openapi.json 与 docs/openapi.yaml，
 * 可用 -Dopenapi.output.file=自定义 JSON 路径（YAML 取其同名 .yaml）
 */
@WebFluxTest(properties = {
    "spring.cloud.bootstrap.enabled=false",
    "spring.cloud.nacos.config.enabled=false",
    "spring.cloud.nacos.discovery.enabled=false",
    "spring.devtools.restart.enabled=false",
    "server.port=8081",
    "springdoc.api-docs.version=openapi_3_1",
    "springdoc.api-docs.path=/v3/api-docs",
})
@AutoConfigureWebTestClient(timeout = "60s")
@Import({
    SwaggerConfig.class,
    SpringDocConfiguration.class,
    SpringDocConfigProperties.class,
    SpringDocSpecPropertiesConfiguration.class,
    SpringDocWebFluxConfiguration.class,
    OpenApiDocGenerator.MockConfiguration.class })
class OpenApiDocGenerator {

    /** 生成产物路径，默认落在 Spring 模块自身的 docs/openapi.json */
    private static final String DEFAULT_OUTPUT_FILE = "docs/openapi.json";

    private static final String API_DOCS_PATH = "/v3/api-docs";

    @Autowired
    private WebTestClient webTestClient;

    @Test
    void generateOpenApiDoc() throws Exception {
        byte[] body = webTestClient.get()
            .uri(API_DOCS_PATH)
            .exchange()
            .expectStatus().isOk()
            .expectBody()
            .returnResult()
            .getResponseBody();

        if (body == null || body.length == 0) {
            throw new IllegalStateException("未能从 " + API_DOCS_PATH + " 获取 OpenAPI 文档内容");
        }

        // 缩进固定用 \n：Jackson 默认跟随平台换行符，Windows 下会写出 CRLF，与仓库的 LF 约定冲突
        DefaultIndenter indenter = new DefaultIndenter("  ", "\n");
        DefaultPrettyPrinter prettyPrinter = new DefaultPrettyPrinter();
        prettyPrinter.indentObjectsWith(indenter);
        prettyPrinter.indentArraysWith(indenter);

        ObjectMapper mapper = new ObjectMapper();
        mapper.setDefaultPrettyPrinter(prettyPrinter);
        JsonNode document = mapper.readTree(new String(body, StandardCharsets.UTF_8));

        // 与 GoZero 的 fix.py 保持一致：落盘前移除 servers
        // 网关才是真实入口，写死 localhost:8081 会让 Apifox 用错地址，Base URL 统一交给 Apifox 环境面板维护
        if (document instanceof ObjectNode objectNode) {
            objectNode.remove("servers");
            normalizeVoidDataSchema(objectNode);
        }
        String json = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(document);

        Path output = Path.of(System.getProperty("openapi.output.file", DEFAULT_OUTPUT_FILE));
        Path parent = output.toAbsolutePath().getParent();
        if (parent != null) {
            Files.createDirectories(parent);
        }
        // 固定用 \n 落盘，避免 Windows 下生成 CRLF 与仓库的 LF 约定冲突
        Files.writeString(output, json + "\n", StandardCharsets.UTF_8);

        // 同时输出 YAML，便于人工查看与 diff
        Path yamlOutput = resolveYamlOutput(output);
        Files.writeString(yamlOutput, toYaml(document), StandardCharsets.UTF_8);
    }

    private static void normalizeVoidDataSchema(ObjectNode document) {
        JsonNode schemas = document.path("components").path("schemas");
        if (!schemas.isObject()) {
            return;
        }
        schemas.fields().forEachRemaining(entry -> {
            if (!entry.getKey().endsWith("Void")) {
                return;
            }
            JsonNode data = entry.getValue().path("properties").path("data");
            if (data instanceof ObjectNode dataSchema
                && "返回数据".equals(dataSchema.path("description").asText())) {
                dataSchema.put("type", "null");
            }
        });
    }

    /** 序列化为 YAML，并去掉 Jackson 默认写出的文档起始标记，与其余三个服务的产物保持一致 */
    private static String toYaml(JsonNode document) throws JsonProcessingException {
        String yaml = new YAMLMapper().writeValueAsString(document);
        if (yaml.startsWith("---")) {
            yaml = yaml.substring(yaml.indexOf('\n') + 1);
        }
        return yaml;
    }

    /** 由 JSON 产物路径推导同目录下的 YAML 产物路径 */
    private static Path resolveYamlOutput(Path jsonOutput) {
        String fileName = jsonOutput.getFileName().toString();
        int dotIndex = fileName.lastIndexOf('.');
        String baseName = dotIndex > 0 ? fileName.substring(0, dotIndex) : fileName;
        Path parent = jsonOutput.getParent();
        return parent == null ? Path.of(baseName + ".yaml") : parent.resolve(baseName + ".yaml");
    }

    /**
     * 为 Web 层缺失的依赖注册 Mockito 替身
     *
     * 扫描 Controller 与 ControllerAdvice 的构造器参数，凡是在当前上下文里找不到的依赖，
     * 一律注册为 Mock 实例，从而彻底切断对业务层与基础设施层的依赖
     */
    static class AutoMockBeanFactoryPostProcessor implements BeanFactoryPostProcessor {

        /** 扫描范围与 @Starter 的组件扫描根保持一致 */
        private static final String BASE_PACKAGE = "com.hcsy.spring";

        private final Set<Class<?>> mockedTypes = new LinkedHashSet<>();

        @Override
        public void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
            if (!(beanFactory instanceof BeanDefinitionRegistry registry)) {
                return;
            }
            for (Class<?> webComponent : scanWebComponents()) {
                for (Constructor<?> constructor : webComponent.getDeclaredConstructors()) {
                    for (Class<?> parameterType : constructor.getParameterTypes()) {
                        registerMockIfMissing(beanFactory, registry, parameterType);
                    }
                }
            }
        }

        private Set<Class<?>> scanWebComponents() {
            ClassPathScanningCandidateComponentProvider scanner = new ClassPathScanningCandidateComponentProvider(
                false);
            scanner.addIncludeFilter(new AnnotationTypeFilter(Controller.class));
            scanner.addIncludeFilter(new AnnotationTypeFilter(ControllerAdvice.class));

            Set<Class<?>> components = new LinkedHashSet<>();
            scanner.findCandidateComponents(BASE_PACKAGE).forEach(definition -> {
                try {
                    components.add(Class.forName(definition.getBeanClassName()));
                } catch (ClassNotFoundException ignored) {
                    // 扫描到的类一定会被当前类加载器加载，这里无需处理
                }
            });
            return components;
        }

        private void registerMockIfMissing(ConfigurableListableBeanFactory beanFactory, BeanDefinitionRegistry registry,
            Class<?> parameterType) {
            // 只处理项目自身的依赖类型：基本类型、数组、JDK 内置类型与 final 类（Mockito 无法替身）全部跳过
            if (parameterType.isPrimitive() || parameterType.isArray() || Modifier.isFinal(parameterType.getModifiers())
                || parameterType.getName().startsWith("java.") || parameterType.getName().startsWith("javax.")) {
                return;
            }
            if (mockedTypes.contains(parameterType)) {
                return;
            }
            if (beanFactory.getBeanNamesForType(parameterType, true, false).length > 0) {
                return;
            }

            mockedTypes.add(parameterType);
            RootBeanDefinition definition = new RootBeanDefinition(parameterType);
            definition.setInstanceSupplier(() -> Mockito.mock(parameterType));
            registry.registerBeanDefinition("autoMocked$" + parameterType.getName(), definition);
        }
    }

    /**
     * 测试装配：把自动 Mock 处理器挂成静态 @Bean，避免 @Configuration 类被提前实例化
     */
    @TestConfiguration
    static class MockConfiguration {

        @Bean
        static BeanFactoryPostProcessor autoMockBeanFactoryPostProcessor() {
            return new AutoMockBeanFactoryPostProcessor();
        }
    }
}
