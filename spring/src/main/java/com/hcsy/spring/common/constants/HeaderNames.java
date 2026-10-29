package com.hcsy.spring.common.constants;

/**
 * 网关与微服务间透传的自定义 HTTP 请求头
 */
public final class HeaderNames {
    // ===== 请求头名称 =====

    /** 网关透传的访问令牌请求头 */
    public static final String ACCESS_TOKEN = "X-Access-Token";
    /** 网关透传的原始请求路径请求头 */
    public static final String FORWARDED_URI = "X-Forwarded-Uri";
    /** 网关透传的用户 ID 请求头 */
    public static final String USER_ID = "X-User-Id";
    /** 网关透传的用户名请求头 */
    public static final String USERNAME = "X-Username";
    /** 网关透传的会话 ID 请求头 */
    public static final String SESSION_ID = "X-Session-Id";

    /**
     * 聚合网关与微服务间透传的自定义 HTTP 请求头名称常量
     */
    private HeaderNames() {
    }
}
