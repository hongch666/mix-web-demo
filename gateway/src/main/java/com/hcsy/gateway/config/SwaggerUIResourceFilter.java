package com.hcsy.gateway.config;

import java.nio.charset.StandardCharsets;

import org.springframework.core.Ordered;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.core.io.buffer.DataBufferUtils;
import org.springframework.http.MediaType;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;

import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Mono;

/**
 * Swagger UI 静态资源过滤器
 * 在认证过滤器之前直接处理 /swagger-ui/** 请求，从 classpath 读取静态资源返回
 */
@Component
@Slf4j
public class SwaggerUIResourceFilter implements WebFilter, Ordered {

    private static final String SWAGGER_UI_PREFIX = "/swagger-ui/";

    @Override
    public int getOrder() {
        // 在 AuthGlobalFilter(-100) 之前执行
        return Ordered.HIGHEST_PRECEDENCE - 200;
    }

    @SuppressWarnings("null")
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        String path = exchange.getRequest().getURI().getPath();

        if (!path.startsWith(SWAGGER_UI_PREFIX)) {
            return chain.filter(exchange);
        }

        // 确定资源路径：/swagger-ui/ 或 /swagger-ui -> index.html
        // /swagger-ui/xxx.css -> static/swagger-ui/xxx.css
        String relativePath = path.equals(SWAGGER_UI_PREFIX) || path.equals("/swagger-ui")
                ? "static/swagger-ui/index.html"
                : "static/swagger-ui/" + path.substring(SWAGGER_UI_PREFIX.length());

        Resource resource = new ClassPathResource(relativePath);
        if (!resource.exists()) {
            log.warn("Swagger UI 资源不存在: {}", relativePath);
            return chain.filter(exchange);
        }

        MediaType mediaType = getMediaType(relativePath);
        ServerHttpResponse response = exchange.getResponse();
        response.getHeaders().setContentType(mediaType);

        // 从资源文件读取内容并写入响应
        return DataBufferUtils.readInputStream(resource::getInputStream, response.bufferFactory(), 4096)
                .reduce(DataBuffer::write)
                .flatMap(buffer -> {
                    response.getHeaders().setContentLength(buffer.readableByteCount());
                    return response.writeWith(Mono.just(buffer));
                })
                .doOnError(error -> log.error("读取 Swagger UI 资源失败: {}", relativePath, error))
                .then();
    }

    @SuppressWarnings("null")
    private MediaType getMediaType(String filename) {
        if (filename.endsWith(".css")) {
            return new MediaType("text", "css", StandardCharsets.UTF_8);
        }
        if (filename.endsWith(".js")) {
            return new MediaType("application", "javascript", StandardCharsets.UTF_8);
        }
        if (filename.endsWith(".png")) {
            return MediaType.IMAGE_PNG;
        }
        if (filename.endsWith(".ico")) {
            return new MediaType("image", "x-icon");
        }
        return new MediaType("text", "html", StandardCharsets.UTF_8);
    }
}
