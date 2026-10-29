package com.hcsy.spring.common.constants;

/**
 * 配置默认值类 — AI用户ID/名称/头像、锁过期时间等
 */
public class Defaults {

    /**
     * 聚合默认文案、AI用户配置、缓存 TTL 与分布式锁过期时间等默认值常量
     */
    private Defaults() {
    }

    // ===== 默认值 =====

    /** 文章信息缺失时使用的兜底名称 */
    public static final String DEFAULT_ARTICLE = "未知文章";
    /** 用户信息缺失时使用的兜底名称 */
    public static final String DEFAULT_USER = "未知用户";
    /** 用户信息缺失时使用的兜底用户 ID */
    public static final String DEFAULT_USER_ID = "0";
    /** AI 用户信息缺失时使用的兜底名称 */
    public static final String DEFAULT_AI = "未知AI";
    /** 服务连通性测试返回的固定消息 */
    public static final String TEST = "Hello,I am Spring!";

    // ===== AI 用户配置 =====

    /** Claude 评论作者的固定用户 ID */
    public static final long CLAUDE_ID = 1001L;
    /** Claude 评论作者的名称 */
    public static final String CLAUDE_NAME = "Claude";
    /** Claude 评论作者的邮箱 */
    public static final String CLAUDE_EMAIL = "claude@example.com";
    /** Claude 评论作者的头像地址 */
    public static final String CLAUDE_IMG = "https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/claude.png";
    /** Gemini 评论作者的固定用户 ID */
    public static final long GEMINI_ID = 1002L;
    /** Gemini 评论作者的名称 */
    public static final String GEMINI_NAME = "Gemini";
    /** Gemini 评论作者的邮箱 */
    public static final String GEMINI_EMAIL = "gemini@example.com";
    /** Gemini 评论作者的头像地址 */
    public static final String GEMINI_IMG = "https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/gemini.jpeg";
    /** GPT 评论作者的固定用户 ID */
    public static final long GPT_ID = 1003L;
    /** GPT 评论作者的名称 */
    public static final String GPT_NAME = "GPT";
    /** GPT 评论作者的邮箱 */
    public static final String GPT_EMAIL = "gpt@example.com";
    /** GPT 评论作者的头像地址 */
    public static final String GPT_IMG = "https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/gpt.png";
    /** DeepSeek 评论作者的固定用户 ID */
    public static final long DEEPSEEK_ID = 1004L;
    /** DeepSeek 评论作者的名称 */
    public static final String DEEPSEEK_NAME = "DeepSeek";
    /** DeepSeek 评论作者的邮箱 */
    public static final String DEEPSEEK_EMAIL = "deepseek@example.com";
    /** DeepSeek 评论作者的头像地址 */
    public static final String DEEPSEEK_IMG = "https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/deepseek.png";
    /** GLM 评论作者的固定用户 ID */
    public static final long GLM_ID = 1005L;
    /** GLM 评论作者的名称 */
    public static final String GLM_NAME = "GLM";
    /** GLM 评论作者的邮箱 */
    public static final String GLM_EMAIL = "glm@example.com";
    /** GLM 评论作者的头像地址 */
    public static final String GLM_IMG = "https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/glm.png";
    /** Qwen 评论作者的固定用户 ID */
    public static final long QWEN_ID = 1006L;
    /** Qwen 评论作者的名称 */
    public static final String QWEN_NAME = "Qwen";
    /** Qwen 评论作者的邮箱 */
    public static final String QWEN_EMAIL = "qwen@example.com";
    /** Qwen 评论作者的头像地址 */
    public static final String QWEN_IMG = "https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/qwen.png";
    /** 日志与响应中隐藏密码时使用的掩码 */
    public static final String HIDE_PASSWORD = "******";

    // ===== 启动 =====

    /** 开发环境服务监听的默认 IP */
    public static final String INIT_IP = "localhost";
    /** 服务启动成功的日志消息 */
    public static final String INIT_MSG = "Spring Boot应用已启动";
    /** 运行模式的日志消息模板 */
    public static final String INIT_MODE = "运行模式: %s";
    /** 服务地址的日志消息模板 */
    public static final String INIT_ADDR = "服务地址: http://%s:%s/";
    /** Swagger 文档地址的日志消息模板 */
    public static final String INIT_SWAGGER_ADDR = "Swagger文档地址: http://%s:%s/swagger-ui/index.html";

    // ===== Swagger =====

    /** 文档标题 */
    public static final String SWAGGER_TITLE = "Spring部分的Swagger文档";
    /** 接口版本号 */
    public static final String SWAGGER_VERSION = "1.0.0";
    /** 文档描述 */
    public static final String SWAGGER_DESC = "这是项目的Spring部分的Swagger文档";
    /** 文档中服务地址的固定前缀 */
    public static final String SWAGGER_URL_PREFIX = "http://localhost:";

    // ===== 分布式锁配置 =====

    /** 过期 Token 清理任务的分布式锁过期秒数 */
    public static final long LOCK_TASK_TOKEN_CLEANUP_EXPIRE = 3600L;
    /** 刷新令牌换发锁的过期秒数 */
    public static final long LOCK_TOKEN_REFRESH_EXPIRE = 10L;

    // ===== 用户角色 =====

    /** AI 用户的角色标识 */
    public static final String AI_ROLE = "ai";

    // ===== GitHub OAuth 票据过期时间（秒） =====

    /** GitHub 登录票据的缓存有效期秒数 */
    public static final long GITHUB_TOKEN_TICKET_TTL_SECONDS = 60L;

    // ===== 多级缓存 TTL（秒） =====

    // 所有缓存统一：L1 为本地 Caffeine，L2 为 Redis
    // L1 应短于 L2，以缩小跨实例失效广播漏收时的脏数据窗口
    public static final long CACHE_L1_TTL_SECONDS = 5 * 60L;
    /** Redis 二级缓存存活秒数，需长于 L1 */
    public static final long CACHE_L2_TTL_SECONDS = 24 * 60 * 60L;

    // ===== Neo4j 同步 =====

    /**
     * Neo4j 同步单次抓取上限，点赞/收藏等表数据量可达百万级
     * 全量同步仅取最近若干条，避免一次性加载全部导致耗时过长
     */
    public static final int NEO4J_SYNC_LIMIT = 10_000;
}
