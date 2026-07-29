package com.hcsy.gateway.common.constants;

/**
 * 网关侧所有 Redis key 的唯一来源。
 *
 * <p>其中 {@code userAccess / userSession / userStatus} 与 spring 服务共享同一套鉴权 key 约定，
 * 字符串前缀必须保持一致，否则会导致网关认证与业务服务存储失配。其余限流相关 key 仅网关使用。
 */
public final class RedisKeys {

    private RedisKeys() {
    }

    // ===== 与 spring 服务共享的鉴权 key（前缀必须与 spring RedisKeys 一致）=====

    public static String userAccess(String token) {
        return "user:access:" + token;
    }

    public static String userSession(Long userId, String sessionId) {
        return "user:session:" + userId + ":" + sessionId;
    }

    public static String userStatus(Long userId) {
        return "user:status:" + userId;
    }

    // ===== 限流 key =====

    public static String rateLimit(String path, String clientId) {
        return "rate-limit:" + path + ":" + clientId;
    }

    public static String clientIdUser(String userId) {
        return "user:" + userId;
    }

    public static String clientIdIp(String clientIp) {
        return "ip:" + clientIp;
    }

    public static final String CLIENT_ID_UNKNOWN = "unknown";
}
