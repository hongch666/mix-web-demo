package com.hcsy.spring.common.constants;

/**
 * Redis Key 统一管理类（single source of truth）。
 * 所有 Redis key 的前缀、完整 key 生成方法，以及用于批量扫描的 pattern 都集中在此，
 * 避免 key 前缀在多处硬编码导致漂移 / 失配。
 */
public final class RedisKeys {
    private RedisKeys() {
    }

    // ===== 用户状态 =====
    private static final String USER_STATUS_PREFIX = "user:status:";

    public static String userStatus(Long userId) {
        return USER_STATUS_PREFIX + userId;
    }

    // ===== GitHub OAuth Ticket =====
    private static final String GITHUB_TOKEN_TICKET_PREFIX = "oauth:github:token:";

    public static String githubTokenTicket(String ticket) {
        return GITHUB_TOKEN_TICKET_PREFIX + ticket;
    }

    // ===== 全量用户列表缓存 =====
    private static final String ALL_USERS_CACHE_KEY = "user:page:all-users";

    public static String allUsersCache() {
        return ALL_USERS_CACHE_KEY;
    }

    // ===== 本地缓存失效通知（channel 名称） =====
    private static final String CATEGORY_CACHE_INVALIDATION_CHANNEL = "cache:invalidation:category";
    private static final String USER_CACHE_INVALIDATION_CHANNEL = "cache:invalidation:user";

    public static String categoryCacheInvalidationChannel() {
        return CATEGORY_CACHE_INVALIDATION_CHANNEL;
    }

    public static String userCacheInvalidationChannel() {
        return USER_CACHE_INVALIDATION_CHANNEL;
    }

    // ===== 本地缓存名称（Caffeine cache name） =====
    private static final String ALL_USERS_CACHE_NAME = "all-users";
    private static final String CATEGORY_BY_ID_CACHE_NAME = "category-by-id";
    private static final String CATEGORY_PAGE_CACHE_NAME = "category-page";

    public static String allUsersCacheName() {
        return ALL_USERS_CACHE_NAME;
    }

    public static String categoryByIdCacheName() {
        return CATEGORY_BY_ID_CACHE_NAME;
    }

    public static String categoryPageCacheName() {
        return CATEGORY_PAGE_CACHE_NAME;
    }

    // ===== 分类 =====
    private static final String CATEGORY_BY_ID_PREFIX = "category:byId:";
    private static final String CATEGORY_PREFIX = "category:";

    public static String categoryId(Long categoryId) {
        return CATEGORY_BY_ID_PREFIX + categoryId;
    }

    /** 全量失效分类缓存时使用的 scan pattern */
    public static String categoryAllPattern() {
        return CATEGORY_PREFIX + "*";
    }

    public static String categoryPage(long page, long size) {
        return CATEGORY_PREFIX + "page:p_%d_s_%d".formatted(page, size);
    }

    // ===== 会话 / Token 反向索引 =====
    private static final String USER_SESSION_PREFIX = "user:session:";
    private static final String USER_SESSIONS_PREFIX = "user:sessions:";
    private static final String USER_ACCESS_PREFIX = "user:access:";
    private static final String USER_REFRESH_PREFIX = "user:refresh:";

    public static String userSession(Long userId, String sessionId) {
        return USER_SESSION_PREFIX + userId + ":" + sessionId;
    }

    public static String userSessions(Long userId) {
        return USER_SESSIONS_PREFIX + userId;
    }

    /** cleanupExpiredTokens 扫描所有用户会话时使用的 pattern */
    public static String userSessionsPattern() {
        return USER_SESSIONS_PREFIX + "*";
    }

    public static String userAccess(String accessToken) {
        return USER_ACCESS_PREFIX + accessToken;
    }

    public static String userRefresh(String refreshToken) {
        return USER_REFRESH_PREFIX + refreshToken;
    }

    // ===== 邮箱验证码 / 已验证标记 =====
    private static final String EMAIL_VERIFY_PREFIX = "email:verify:";
    private static final String EMAIL_VERIFIED_PREFIX = EMAIL_VERIFY_PREFIX + "verified:";

    public static String emailVerify(String email) {
        return EMAIL_VERIFY_PREFIX + email;
    }

    public static String emailVerified(String email) {
        return EMAIL_VERIFIED_PREFIX + email;
    }

    // ===== 图形验证码 =====
    private static final String CAPTCHA_PREFIX = "image:captcha:";

    public static String imageCaptcha(String captchaId) {
        return CAPTCHA_PREFIX + captchaId;
    }

    // ===== 分布式锁 =====
    private static final String LOCK_TASK_TOKEN_CLEANUP = "lock:task:token:cleanup";

    public static String lockTaskTokenCleanup() {
        return LOCK_TASK_TOKEN_CLEANUP;
    }
}
