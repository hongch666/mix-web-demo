package com.hcsy.spring.common.constants;

/**
 * Redis Key 统一管理类（single source of truth）
 * 所有 Redis key 的前缀、完整 key 生成方法，以及用于批量扫描的 pattern 都集中在此，避免 key 前缀在多处硬编码导致漂移 / 失配
 */
public final class RedisKeys {
    /**
     * 统一管理 Redis key 前缀、完整 key 生成方法与批量扫描 pattern
     */
    private RedisKeys() {
    }

    // ===== 用户状态 =====

    /** 用户在线状态 key 的前缀 */
    private static final String USER_STATUS_PREFIX = "user:status:";

    /** 生成用户在线状态的 Redis key */
    public static String userStatus(Long userId) {
        return USER_STATUS_PREFIX + userId;
    }

    // ===== GitHub OAuth Ticket =====

    /** GitHub 登录票据 key 的前缀 */
    private static final String GITHUB_TOKEN_TICKET_PREFIX = "oauth:github:token:";

    /** 生成 GitHub 登录票据的 Redis key */
    public static String githubTokenTicket(String ticket) {
        return GITHUB_TOKEN_TICKET_PREFIX + ticket;
    }

    // ===== 全量用户列表缓存 =====

    /** 全量用户列表缓存的 Redis key */
    private static final String ALL_USERS_CACHE_KEY = "user:page:all-users";
    /** 用户角色缓存 key 的前缀 */
    private static final String USER_ROLE_PREFIX = "user:role:";
    /** 用户角色本地缓存名称 */
    private static final String USER_ROLE_CACHE_NAME = "user-role";

    /** 返回全量用户列表缓存的 key */
    public static String allUsersCache() {
        return ALL_USERS_CACHE_KEY;
    }

    // ===== 用户角色缓存 =====

    /** 生成用户角色缓存的 Redis key */
    public static String userRole(Long userId) {
        return USER_ROLE_PREFIX + userId;
    }

    /**
     * 返回用户角色本地缓存名称
     */
    public static String userRoleCacheName() {
        return USER_ROLE_CACHE_NAME;
    }

    // ===== 本地缓存失效通知（channel 名称） =====

    /** 分类本地缓存失效通知的频道名 */
    private static final String CATEGORY_CACHE_INVALIDATION_CHANNEL = "cache:invalidation:category";
    /** 用户本地缓存失效通知的频道名 */
    private static final String USER_CACHE_INVALIDATION_CHANNEL = "cache:invalidation:user";

    /** 返回分类本地缓存失效通知的频道名 */
    public static String categoryCacheInvalidationChannel() {
        return CATEGORY_CACHE_INVALIDATION_CHANNEL;
    }

    /**
     * 返回用户本地缓存失效通知的 Redis 频道名
     */
    public static String userCacheInvalidationChannel() {
        return USER_CACHE_INVALIDATION_CHANNEL;
    }

    // ===== 本地缓存名称（Caffeine cache name） =====

    /** 全量用户列表本地缓存名称 */
    private static final String ALL_USERS_CACHE_NAME = "all-users";
    /** 分类详情本地缓存名称 */
    private static final String CATEGORY_BY_ID_CACHE_NAME = "category-by-id";
    /** 分类分页本地缓存名称 */
    private static final String CATEGORY_PAGE_CACHE_NAME = "category-page";

    /** 返回全量用户列表本地缓存名称 */
    public static String allUsersCacheName() {
        return ALL_USERS_CACHE_NAME;
    }

    /**
     * 返回分类详情本地缓存名称
     */
    public static String categoryByIdCacheName() {
        return CATEGORY_BY_ID_CACHE_NAME;
    }

    /**
     * 返回分类分页本地缓存名称
     */
    public static String categoryPageCacheName() {
        return CATEGORY_PAGE_CACHE_NAME;
    }

    // ===== 分类 =====

    /** 分类详情 key 的前缀 */
    private static final String CATEGORY_BY_ID_PREFIX = "category:byId:";
    /** 分类 key 的公共前缀 */
    private static final String CATEGORY_PREFIX = "category:";

    /** 生成分类详情的 Redis key */
    public static String categoryId(Long categoryId) {
        return CATEGORY_BY_ID_PREFIX + categoryId;
    }

    /** 全量失效分类缓存时使用的 scan pattern */
    public static String categoryAllPattern() {
        return CATEGORY_PREFIX + "*";
    }

    /**
     * 生成分类分页结果缓存的 Redis key
     */
    public static String categoryPage(long page, long size) {
        return CATEGORY_PREFIX + "page:p_%d_s_%d".formatted(page, size);
    }

    // ===== 会话 / Token 反向索引 =====

    /** 用户单个会话 key 的前缀 */
    private static final String USER_SESSION_PREFIX = "user:session:";
    /** 用户会话集合 key 的前缀 */
    private static final String USER_SESSIONS_PREFIX = "user:sessions:";
    /** 访问令牌反向索引 key 的前缀 */
    private static final String USER_ACCESS_PREFIX = "user:access:";
    /** 刷新令牌反向索引 key 的前缀 */
    private static final String USER_REFRESH_PREFIX = "user:refresh:";

    /** 生成用户会话的 Redis key */
    public static String userSession(Long userId, String sessionId) {
        return USER_SESSION_PREFIX + userId + ":" + sessionId;
    }

    /**
     * 生成用户全部登录会话反向索引的 Redis key
     */
    public static String userSessions(Long userId) {
        return USER_SESSIONS_PREFIX + userId;
    }

    /** cleanupExpiredTokens 扫描所有用户会话时使用的 pattern */
    public static String userSessionsPattern() {
        return USER_SESSIONS_PREFIX + "*";
    }

    /**
     * 生成访问令牌到会话反向索引的 Redis key
     */
    public static String userAccess(String accessToken) {
        return USER_ACCESS_PREFIX + accessToken;
    }

    /**
     * 生成刷新令牌到会话反向索引的 Redis key
     */
    public static String userRefresh(String refreshToken) {
        return USER_REFRESH_PREFIX + refreshToken;
    }

    // ===== 邮箱验证码 / 已验证标记 =====

    /** 邮箱验证码 key 的前缀 */
    private static final String EMAIL_VERIFY_PREFIX = "email:verify:";
    /** 邮箱已验证标记 key 的前缀 */
    private static final String EMAIL_VERIFIED_PREFIX = EMAIL_VERIFY_PREFIX + "verified:";

    /** 生成邮箱验证码的 Redis key */
    public static String emailVerify(String email) {
        return EMAIL_VERIFY_PREFIX + email;
    }

    /**
     * 生成邮箱已验证标记的 Redis key
     */
    public static String emailVerified(String email) {
        return EMAIL_VERIFIED_PREFIX + email;
    }

    // ===== 图形验证码 =====

    /** 图形验证码 key 的前缀 */
    private static final String CAPTCHA_PREFIX = "image:captcha:";

    /** 生成图形验证码的 Redis key */
    public static String imageCaptcha(String captchaId) {
        return CAPTCHA_PREFIX + captchaId;
    }

    // ===== 分布式锁 =====

    /** 过期 Token 清理任务的分布式锁 key */
    private static final String LOCK_TASK_TOKEN_CLEANUP = "lock:task:token:cleanup";
    /** 刷新令牌换发锁 key 的前缀 */
    private static final String LOCK_TOKEN_REFRESH_PREFIX = "lock:token:refresh:";

    /** 返回过期 Token 清理锁的 key */
    public static String lockTaskTokenCleanup() {
        return LOCK_TASK_TOKEN_CLEANUP;
    }

    /**
     * 生成刷新令牌换发分布式锁的 Redis key
     */
    public static String lockTokenRefresh(String refreshToken) {
        return LOCK_TOKEN_REFRESH_PREFIX + refreshToken;
    }
}
