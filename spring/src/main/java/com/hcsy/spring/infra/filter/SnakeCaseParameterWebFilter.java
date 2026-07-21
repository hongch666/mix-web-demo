package com.hcsy.spring.infra.filter;

import java.util.LinkedHashMap;
import java.util.Map;

import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.util.MultiValueMap;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;

import reactor.core.publisher.Mono;

/**
 * 兼容 query/form 参数的下划线命名
 * 替代原有的 SnakeCaseParameterFilter (OncePerRequestFilter)
 */
@Component
public class SnakeCaseParameterWebFilter implements WebFilter {

    @SuppressWarnings("null")
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        MultiValueMap<String, String> queryParams = request.getQueryParams();

        if (queryParams.isEmpty()) {
            return chain.filter(exchange);
        }

        Map<String, String[]> modifiedParams = new LinkedHashMap<>();
        for (Map.Entry<String, java.util.List<String>> entry : queryParams.entrySet()) {
            String key = entry.getKey();
            modifiedParams.put(key, entry.getValue().toArray(new String[0]));
            if (key.contains("_")) {
                String camelKey = toCamelCase(key);
                modifiedParams.putIfAbsent(camelKey, entry.getValue().toArray(new String[0]));
            }
        }

        return chain.filter(exchange);
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
