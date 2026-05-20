package com.hcsy.spring.infra.filter;

import java.io.IOException;
import java.util.Collections;
import java.util.Enumeration;
import java.util.LinkedHashMap;
import java.util.Map;

import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletRequestWrapper;
import jakarta.servlet.http.HttpServletResponse;

/**
 * 兼容 query/form 参数的下划线命名。
 *
 * Jackson 的 SNAKE_CASE 只处理 JSON body/response，不处理 @RequestParam 和 @ModelAttribute。
 * 这里在请求参数层补充 camelCase 别名，让 article_title 可以绑定到 articleTitle。
 */
@Component
public class SnakeCaseParameterFilter extends OncePerRequestFilter {

    @SuppressWarnings("null")
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        filterChain.doFilter(new SnakeCaseParameterRequestWrapper(request), response);
    }

    private static class SnakeCaseParameterRequestWrapper extends HttpServletRequestWrapper {
        private final Map<String, String[]> parameterMap;

        SnakeCaseParameterRequestWrapper(HttpServletRequest request) {
            super(request);
            this.parameterMap = buildParameterMap(request.getParameterMap());
        }

        @Override
        public String getParameter(String name) {
            String[] values = parameterMap.get(name);
            return values != null && values.length > 0 ? values[0] : null;
        }

        @Override
        public Map<String, String[]> getParameterMap() {
            return parameterMap;
        }

        @Override
        public Enumeration<String> getParameterNames() {
            return Collections.enumeration(parameterMap.keySet());
        }

        @Override
        public String[] getParameterValues(String name) {
            return parameterMap.get(name);
        }

        private static Map<String, String[]> buildParameterMap(Map<String, String[]> source) {
            Map<String, String[]> result = new LinkedHashMap<>(source);
            for (Map.Entry<String, String[]> entry : source.entrySet()) {
                String key = entry.getKey();
                if (!key.contains("_")) {
                    continue;
                }
                String camelKey = toCamelCase(key);
                result.putIfAbsent(camelKey, entry.getValue());
            }
            return result;
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
}
