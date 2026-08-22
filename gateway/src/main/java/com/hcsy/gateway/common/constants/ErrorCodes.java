package com.hcsy.gateway.common.constants;

/**
 * 错误标识常量
 */
public class ErrorCodes {

    private ErrorCodes() {
    }

    // ===== 401 Unauthorized =====
    public static final String TOKEN_EXPIRED = "TOKEN_EXPIRED";
    public static final String TOKEN_INVALID = "TOKEN_INVALID";
    public static final String TOKEN_TYPE_INVALID = "TOKEN_TYPE_INVALID";
    public static final String USER_NOT_LOGIN = "USER_NOT_LOGIN";

    // ===== 429 Too Many Requests =====
    public static final String RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED";

    // ===== 500 Internal Server Error =====
    public static final String GATEWAY_SERVER_ERROR = "GATEWAY_SERVER_ERROR";

    // ===== 502 Bad Gateway =====
    public static final String SERVICE_CALL_FAILED = "SERVICE_CALL_FAILED";

    // ===== 503 Service Unavailable =====
    public static final String NO_AVAILABLE_SERVICE_INSTANCE = "NO_AVAILABLE_SERVICE_INSTANCE";
    public static final String REDIS_UNAVAILABLE = "REDIS_UNAVAILABLE";

    // ===== 504 Gateway Timeout =====
    public static final String REQUEST_TIMEOUT = "REQUEST_TIMEOUT";

    // ===== 500 Internal Server Error（认证流程中非预期异常） =====
    public static final String AUTH_UNEXPECTED_ERROR = "AUTH_UNEXPECTED_ERROR";

    // ===== 默认消息 =====
    public static final String DEFAULT_ERROR_MSG = "网关服务错误";
}
