package com.hcsy.gateway.common;

public class Constants {

    private Constants() {}

    // ===== 401 Unauthorized =====
    public static final String TOKEN_EXPIRED = "TOKEN_EXPIRED";
    public static final String TOKEN_INVALID = "TOKEN_INVALID";
    public static final String TOKEN_TYPE_INVALID = "TOKEN_TYPE_INVALID";
    public static final String USER_NOT_LOGIN = "USER_NOT_LOGIN";

    // ===== 403 Forbidden =====
    public static final String INTERNAL_TOKEN_SERVICE_MISMATCH = "INTERNAL_TOKEN_SERVICE_MISMATCH";

    // ===== 429 Too Many Requests =====
    public static final String RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED";

    // ===== 500 Internal Server Error =====
    public static final String GATEWAY_SERVER_ERROR = "GATEWAY_SERVER_ERROR";
    public static final String INTERNAL_TOKEN_SECRET_NOT_NULL = "INTERNAL_TOKEN_SECRET_NOT_NULL";

    // ===== 502 Bad Gateway =====
    public static final String SERVICE_CALL_FAILED = "SERVICE_CALL_FAILED";

    // ===== 503 Service Unavailable =====
    public static final String SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE";
    public static final String NO_AVAILABLE_SERVICE_INSTANCE = "NO_AVAILABLE_SERVICE_INSTANCE";

    // ===== 504 Gateway Timeout =====
    public static final String REQUEST_TIMEOUT = "REQUEST_TIMEOUT";

    // ===== 内部服务令牌错误 =====
    public static final String INTERNAL_TOKEN_MISSING = "INTERNAL_TOKEN_MISSING";
    public static final String INTERNAL_TOKEN_INVALID = "INTERNAL_TOKEN_INVALID";
    public static final String INTERNAL_TOKEN_EXPIRED = "INTERNAL_TOKEN_EXPIRED";

    // ===== 默认消息 =====
    public static final String DEFAULT_ERROR_MSG = "网关服务错误";
}
