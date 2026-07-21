package com.hcsy.spring.infra.interceptor;

import org.springframework.stereotype.Component;

import com.hcsy.spring.common.constants.HttpCode;
import com.hcsy.spring.common.constants.Messages;
import com.hcsy.spring.common.exceptions.BusinessException;
import com.hcsy.spring.common.utils.InternalTokenUtil;
import com.hcsy.spring.common.utils.SimpleLogger;

import feign.RequestInterceptor;
import feign.RequestTemplate;
import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class DefaultHeaderInterceptor implements RequestInterceptor {

    private final InternalTokenUtil internalTokenUtil;
    private final SimpleLogger logger;

    private static final String INTERNAL_TOKEN_HEADER = "X-Internal-Token";
    private static final String BEARER_PREFIX = "Bearer ";
    private static final String SERVICE_NAME = "spring"; // 当前服务名称

    // 使用 ThreadLocal 在 Feign 调用线程中传递用户信息
    // 由调用方在发起 Feign 调用前从 Reactor Context 提取并设置
    private static final ThreadLocal<Long> USER_ID_HOLDER = new ThreadLocal<>();
    private static final ThreadLocal<String> USERNAME_HOLDER = new ThreadLocal<>();

    public static void setUserContext(Long userId, String username) {
        USER_ID_HOLDER.set(userId);
        USERNAME_HOLDER.set(username);
    }

    public static void clearUserContext() {
        USER_ID_HOLDER.remove();
        USERNAME_HOLDER.remove();
    }

    @Override
    public void apply(RequestTemplate template) {
        // 从 ThreadLocal 获取用户信息（由调用方在 Feign 调用前设置）
        Long userId = USER_ID_HOLDER.get();
        String username = USERNAME_HOLDER.get();

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
            logger.error(Messages.TOKEN_GEN_FAIL + e.getMessage());
            throw BusinessException.builder().httpStatus(HttpCode.UNAUTHORIZED).errorMessage(Messages.TOKEN_GEN_FAIL).build();
        } finally {
            // 清除 ThreadLocal，避免内存泄漏
            clearUserContext();
        }
    }
}
