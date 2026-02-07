package com.hcsy.spring.common.interceptor;

import org.springframework.stereotype.Component;

import com.hcsy.spring.common.utils.InternalTokenUtil;
import com.hcsy.spring.common.utils.UserContext;

import feign.RequestInterceptor;
import feign.RequestTemplate;
import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class DefaultHeaderInterceptor implements RequestInterceptor {

    private final InternalTokenUtil internalTokenUtil;

    private static final String INTERNAL_TOKEN_HEADER = "X-Internal-Token";
    private static final String BEARER_PREFIX = "Bearer ";
    private static final String SERVICE_NAME = "spring"; // 当前服务名称

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

        // 添加内部服务令牌（调用其他微服务时使用）
        // 即使 userId 为 null，也需要生成令牌以便微服务间通信
        try {
            Long tokenUserId = userId != null ? userId : -1L; // 使用 -1 表示系统调用
            String internalToken = internalTokenUtil.generateInternalToken(tokenUserId, SERVICE_NAME);
            template.header(INTERNAL_TOKEN_HEADER, BEARER_PREFIX + internalToken);
        } catch (Exception e) {
            // 令牌生成失败，记录日志但不影响正常请求
            // 可根据需求决定是否继续或抛出异常
        }
    }
}
