package com.hcsy.spring.common.constants;

/**
 * 同步资源常量
 * 统一 Spring、GoZero、FastAPI 三端的资源命名，与数仓源表 key、Neo4j 主体保持一致
 */
public final class SyncResource {

    /**
     * 私有构造器，防止常量类被实例化
     */
    private SyncResource() {
    }

    // ===== 同步资源名 =====

    /** 同步资源名：文章 */
    public static final String ARTICLES = "articles";
    /** 同步资源名：用户 */
    public static final String USER = "user";
    /** 同步资源名：分类 */
    public static final String CATEGORY = "category";
    /** 同步资源名：子分类 */
    public static final String SUB_CATEGORY = "sub_category";
    /** 同步资源名：点赞 */
    public static final String LIKES = "likes";
    /** 同步资源名：收藏 */
    public static final String COLLECTS = "collects";
    /** 同步资源名：评论 */
    public static final String COMMENTS = "comments";
    /** 同步资源名：关注 */
    public static final String FOCUS = "focus";
}
