package com.hcsy.spring.interceptor;

import org.springframework.stereotype.Component;

import com.hcsy.spring.utils.UserContext;

import feign.RequestInterceptor;
import feign.RequestTemplate;

@Component
public class DefaultHeaderInterceptor implements RequestInterceptor {
    @Override
    public void apply(RequestTemplate template) {
        // 添加默认请求头
        Long userId = UserContext.getUserId();
        String username = UserContext.getUsername();
        template.header("X-User-Id", userId.toString());
        template.header("X-Username", username);
    }
}
