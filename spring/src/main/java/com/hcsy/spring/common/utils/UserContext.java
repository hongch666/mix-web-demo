package com.hcsy.spring.common.utils;

import reactor.util.context.Context;
import reactor.util.context.ContextView;

/**
 * 基于 Reactor Context 的请求上下文
 * 替代原有的 InheritableThreadLocal 实现
 */
public class UserContext {

    public static final String CONTEXT_KEY_USER_ID = "userId";
    public static final String CONTEXT_KEY_USERNAME = "username";
    public static final String CONTEXT_KEY_SESSION_ID = "sessionId";
    public static final String CONTEXT_KEY_TOKEN = "token";
    public static final String CONTEXT_KEY_INTERNAL_TOKEN = "internalToken";

    /**
     * 将用户信息写入 Reactor Context
     */
    public static Context writeContext(Context ctx, Long userId, String username,
                                       String sessionId, String token, String internalToken) {
        if (userId != null) ctx = ctx.put(CONTEXT_KEY_USER_ID, userId);
        if (username != null) ctx = ctx.put(CONTEXT_KEY_USERNAME, username);
        if (sessionId != null) ctx = ctx.put(CONTEXT_KEY_SESSION_ID, sessionId);
        if (token != null) ctx = ctx.put(CONTEXT_KEY_TOKEN, token);
        if (internalToken != null) ctx = ctx.put(CONTEXT_KEY_INTERNAL_TOKEN, internalToken);
        return ctx;
    }

    /**
     * 从 Reactor Context 中获取 userId
     */
    public static Long getUserId(ContextView ctx) {
        return ctx.getOrDefault(CONTEXT_KEY_USER_ID, null);
    }

    /**
     * 从 Reactor Context 中获取 username
     */
    public static String getUsername(ContextView ctx) {
        return ctx.getOrDefault(CONTEXT_KEY_USERNAME, null);
    }

    /**
     * 从 Reactor Context 中获取 token
     */
    public static String getToken(ContextView ctx) {
        return ctx.getOrDefault(CONTEXT_KEY_TOKEN, null);
    }

    /**
     * 从 Reactor Context 中获取 sessionId
     */
    public static String getSessionId(ContextView ctx) {
        return ctx.getOrDefault(CONTEXT_KEY_SESSION_ID, null);
    }

    public static String getInternalToken(ContextView ctx) {
        return ctx.getOrDefault(CONTEXT_KEY_INTERNAL_TOKEN, null);
    }
}
