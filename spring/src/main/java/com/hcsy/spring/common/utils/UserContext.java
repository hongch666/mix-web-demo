package com.hcsy.spring.common.utils;

public class UserContext {
    // 使用 InheritableThreadLocal 支持父子线程传递
    private static final InheritableThreadLocal<Long> userIdHolder = new InheritableThreadLocal<>();
    private static final InheritableThreadLocal<String> usernameHolder = new InheritableThreadLocal<>();

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

    public static void clear() {
        userIdHolder.remove();
        usernameHolder.remove();
    }
}
