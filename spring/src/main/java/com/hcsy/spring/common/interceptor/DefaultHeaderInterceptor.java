package com.hcsy.spring.common.interceptor;

import org.springframework.stereotype.Component;

import com.hcsy.spring.common.utils.UserContext;

import feign.RequestInterceptor;
import feign.RequestTemplate;

@Component
public class DefaultHeaderInterceptor implements RequestInterceptor {
    @Override
    public void apply(RequestTemplate template) {
        // 添加默认请求头
        Long userId = UserContext.getUserId();
        String username = UserContext.getUsername();

        // 处理异步任务中 userId 为 null 的情况
        if (userId != null) {
            template.header("X-User-Id", userId.toString());
        }
        if (username != null) {
            template.header("X-Username", username);
        }
    }
}
