package com.hcsy.spring.infra.filter;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;

import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.core.io.buffer.DataBufferUtils;
import org.springframework.http.MediaType;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpRequestDecorator;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/**
 * 兼容 query/form 参数的下划线命名
 * 将形如 user_id 的下划线参数同时以驼峰别名 userId 暴露给控制器
 */
@Component
public class SnakeCaseParameterWebFilter implements WebFilter {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();

        // 处理 query 参数（同步）：补充下划线参数的驼峰别名
        ServerHttpRequest decorated = decorateQueryParams(request);

        // 处理 form 参数（异步）：仅对 application/x-www-form-urlencoded 生效
        Mono<ServerHttpRequest> decoratedMono = decorateFormParams(exchange, decorated);

        return decoratedMono.flatMap(finalRequest -> chain.filter(exchange.mutate().request(finalRequest).build()));
    }

    /**
     * 处理 query 参数：保留原始下划线参数，同时补充驼峰别名。
     * 若无需转换则返回原请求，避免额外包装。
     */
    private ServerHttpRequest decorateQueryParams(ServerHttpRequest request) {
        MultiValueMap<String, String> queryParams = request.getQueryParams();
        if (queryParams.isEmpty() || !containsUnderscore(queryParams)) {
            return request;
        }

        MultiValueMap<String, String> mergedParams = mergeParams(queryParams);
        return new ServerHttpRequestDecorator(request) {
            @Override
            public MultiValueMap<String, String> getQueryParams() {
                return mergedParams;
            }
        };
    }

    /**
     * 处理 form 参数：仅对 application/x-www-form-urlencoded 请求生效。
     * 通过装饰器异步缓冲 body，解码为表单参数，补充下划线驼峰别名后重新编码返回。
     */
    private Mono<ServerHttpRequest> decorateFormParams(ServerWebExchange exchange, ServerHttpRequest request) {
        MediaType contentType = request.getHeaders().getContentType();
        if (contentType == null || !MediaType.APPLICATION_FORM_URLENCODED.isCompatibleWith(contentType)) {
            return Mono.just(request);
        }

        return DataBufferUtils.join(request.getBody())
            .flatMap(buffer -> {
                // 解码原始 form body 为参数集合
                MultiValueMap<String, String> formParams = decodeFormBody(buffer);
                DataBufferUtils.release(buffer);

                if (formParams.isEmpty() || !containsUnderscore(formParams)) {
                    return Mono.just(request);
                }

                // 合并下划线驼峰别名
                MultiValueMap<String, String> mergedParams = mergeParams(formParams);

                // 重新编码为 body 并包装请求
                DataBuffer encoded = exchange.getResponse().bufferFactory()
                    .wrap(encodeFormBody(mergedParams).getBytes(StandardCharsets.UTF_8));

                ServerHttpRequestDecorator decorated = new ServerHttpRequestDecorator(request) {
                    @Override
                    public Flux<DataBuffer> getBody() {
                        return Flux.just(encoded);
                    }
                };
                return Mono.just(decorated);
            })
            .defaultIfEmpty(request);
    }

    /**
     * 解码 form body 数据为参数集合（key -> List<value>）。
     */
    private MultiValueMap<String, String> decodeFormBody(DataBuffer buffer) {
        byte[] bytes = new byte[buffer.readableByteCount()];
        buffer.read(bytes);
        String body = new String(bytes, StandardCharsets.UTF_8);

        MultiValueMap<String, String> formParams = new LinkedMultiValueMap<>();
        if (body.isEmpty()) {
            return formParams;
        }
        String[] pairs = body.split("&");
        for (String pair : pairs) {
            int idx = pair.indexOf('=');
            String key = idx >= 0 ? pair.substring(0, idx) : pair;
            String value = idx >= 0 ? pair.substring(idx + 1) : "";
            formParams.add(key, value);
        }
        return formParams;
    }

    /**
     * 将参数集合重新编码为 form body 字符串。
     */
    private String encodeFormBody(MultiValueMap<String, String> params) {
        StringBuilder sb = new StringBuilder();
        boolean first = true;
        for (Map.Entry<String, List<String>> entry : params.entrySet()) {
            for (String value : entry.getValue()) {
                if (!first) {
                    sb.append('&');
                }
                first = false;
                sb.append(entry.getKey()).append('=').append(value);
            }
        }
        return sb.toString();
    }

    /**
     * 合并参数集合：保留原始下划线参数，同时补充驼峰别名。
     * 已存在显式驼峰参数时不覆盖。
     */
    private MultiValueMap<String, String> mergeParams(MultiValueMap<String, String> source) {
        MultiValueMap<String, String> merged = new LinkedMultiValueMap<>();
        for (Map.Entry<String, List<String>> entry : source.entrySet()) {
            String key = entry.getKey();
            merged.put(key, entry.getValue());
            if (key.contains("_")) {
                String camelKey = toCamelCase(key);
                merged.putIfAbsent(camelKey, entry.getValue());
            }
        }
        return merged;
    }

    private static boolean containsUnderscore(MultiValueMap<String, String> params) {
        for (String key : params.keySet()) {
            if (key.contains("_")) {
                return true;
            }
        }
        return false;
    }

    private static String toCamelCase(String value) {
        StringBuilder builder = new StringBuilder(value.length());
        boolean upperNext = false;
        for (int i = 0; i < value.length(); i++) {
            char ch = value.charAt(i);
            if (ch == '_') {
                upperNext = true;
                continue;
            }
            if (upperNext) {
                builder.append(Character.toUpperCase(ch));
                upperNext = false;
            } else {
                builder.append(ch);
            }
        }
        return builder.toString();
    }
}
