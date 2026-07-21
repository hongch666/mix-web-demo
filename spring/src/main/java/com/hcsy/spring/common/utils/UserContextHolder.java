package com.hcsy.spring.common.utils;

/**
 * 基于 ThreadLocal 的用户上下文桥接
 * 供非响应式路径（如 Service 层同步方法）使用，
 * 由 UserContextWebFilter 在请求开始时设置，结束时清除
 */
public class UserContextHolder {

    private static final ThreadLocal<Long> USER_ID_HOLDER = new ThreadLocal<>();
    private static final ThreadLocal<String> USERNAME_HOLDER = new ThreadLocal<>();
    private static final ThreadLocal<String> SESSION_ID_HOLDER = new ThreadLocal<>();
    private static final ThreadLocal<String> TOKEN_HOLDER = new ThreadLocal<>();

    public static void set(Long userId, String username, String sessionId, String token) {
        if (userId != null) USER_ID_HOLDER.set(userId);
        if (username != null) USERNAME_HOLDER.set(username);
        if (sessionId != null) SESSION_ID_HOLDER.set(sessionId);
        if (token != null) TOKEN_HOLDER.set(token);
    }

    public static Long getUserId() {
        return USER_ID_HOLDER.get();
    }

    public static String getUsername() {
        return USERNAME_HOLDER.get();
    }

    public static String getSessionId() {
        return SESSION_ID_HOLDER.get();
    }

    public static String getToken() {
        return TOKEN_HOLDER.get();
    }

    public static void clear() {
        USER_ID_HOLDER.remove();
        USERNAME_HOLDER.remove();
        SESSION_ID_HOLDER.remove();
        TOKEN_HOLDER.remove();
    }
}
