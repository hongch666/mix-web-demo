package com.hcsy.spring.common.constants;

/**
 * 网关与微服务间透传的自定义 HTTP 请求头。
 */
public final class HeaderNames {
    public static final String ACCESS_TOKEN = "X-Access-Token";
    public static final String FORWARDED_URI = "X-Forwarded-Uri";
    public static final String USER_ID = "X-User-Id";
    public static final String USERNAME = "X-Username";
    public static final String SESSION_ID = "X-Session-Id";

    private HeaderNames() {
    }
}
