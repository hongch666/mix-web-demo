package com.hcsy.spring.common.utils;

public class UserContext {
    private static final InheritableThreadLocal<Long> userIdHolder = new InheritableThreadLocal<>();
    private static final InheritableThreadLocal<String> usernameHolder = new InheritableThreadLocal<>();
    private static final InheritableThreadLocal<String> tokenHolder = new InheritableThreadLocal<>();
    private static final InheritableThreadLocal<String> sessionIdHolder = new InheritableThreadLocal<>();

    public static void setUserId(Long userId) {
        userIdHolder.set(userId);
    }

    public static Long getUserId() {
        return userIdHolder.get();
    }

    public static void setUsername(String username) {
        usernameHolder.set(username);
    }

    public static String getUsername() {
        return usernameHolder.get();
    }

    public static void setToken(String token) {
        tokenHolder.set(token);
    }

    public static String getToken() {
        return tokenHolder.get();
    }

    public static void setSessionId(String sessionId) {
        sessionIdHolder.set(sessionId);
    }

    public static String getSessionId() {
        return sessionIdHolder.get();
    }

    public static void clear() {
        userIdHolder.remove();
        usernameHolder.remove();
        tokenHolder.remove();
        sessionIdHolder.remove();
    }
}
