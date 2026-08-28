package com.hcsy.spring.common.constants;

/**
 * 配置默认值类 — AI用户ID/名称/头像、锁过期时间等
 */
public class Defaults {

    private Defaults() {
    }

    // ===== 默认值 =====
    public static final String DEFAULT_ARTICLE = "未知文章";
    public static final String DEFAULT_USER = "未知用户";
    public static final String DEFAULT_USER_ID = "0";
    public static final String DEFAULT_AI = "未知AI";
    public static final String TEST = "Hello,I am Spring!";

    // ===== AI 用户配置 =====
    public static final long DEEPSEEK_ID = 1001L;
    public static final String DEEPSEEK_NAME = "DeepSeek";
    public static final String DEEPSEEK_EMAIL = "deepseek@example.com";
    public static final String DEEPSEEK_IMG = "https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/deepseek.png";
    public static final long GEMINI_ID = 1002L;
    public static final String GEMINI_NAME = "Gemini";
    public static final String GEMINI_EMAIL = "gemini@example.com";
    public static final String GEMINI_IMG = "https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/gemini.jpeg";
    public static final long GPT_ID = 1003L;
    public static final String GPT_NAME = "GPT";
    public static final String GPT_EMAIL = "gpt@example.com";
    public static final String GPT_IMG = "https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/gpt.png";
    public static final String HIDE_PASSWORD = "******";

    // ===== 启动 =====
    public static final String INIT_IP = "localhost";
    public static final String INIT_PORT = "8081";
    public static final String INIT_MSG = "Spring Boot应用已启动";
    public static final String INIT_ADDR = "服务地址: http://%s:%s/";
    public static final String INIT_SWAGGER_ADDR = "Swagger文档地址: http://%s:%s/swagger-ui/index.html";

    // ===== Swagger =====
    public static final String SWAGGER_TITLE = "Spring部分的Swagger文档";
    public static final String SWAGGER_VERSION = "1.0.0";
    public static final String SWAGGER_DESC = "这是项目的Spring部分的Swagger文档";
    public static final String SWAGGER_URL_PREFIX = "http://localhost:";

    // ===== 分布式锁配置 =====
    public static final long LOCK_TASK_TOKEN_CLEANUP_EXPIRE = 3600L;

    // ===== 用户角色 =====
    public static final String AI_ROLE = "ai";

    // ===== GitHub OAuth 票据过期时间（秒） =====
    public static final long GITHUB_TOKEN_TICKET_TTL_SECONDS = 60L;

    // ===== 多级缓存 TTL（秒） =====
    // 所有缓存统一：L1 为本地 Caffeine，L2 为 Redis
    // L1 应短于 L2，以缩小跨实例失效广播漏收时的脏数据窗口
    public static final long CACHE_L1_TTL_SECONDS = 5 * 60L;
    public static final long CACHE_L2_TTL_SECONDS = 24 * 60 * 60L;

    // ===== Neo4j 同步 =====
    /**
     * Neo4j 同步单次抓取上限。点赞/收藏等表数据量可达百万级，
     * 全量同步仅取最近若干条，避免一次性加载全部导致耗时过长。
     */
    public static final int NEO4J_SYNC_LIMIT = 10_000;
}
