package com.hcsy.spring.common.constants;

/**
 * 同步资源常量
 * 统一 Spring、GoZero、FastAPI 三端的资源命名，与数仓源表 key、Neo4j 主体保持一致
 */
public final class SyncResource {

    private SyncResource() {
    }

    public static final String ARTICLES = "articles";
    public static final String USER = "user";
    public static final String CATEGORY = "category";
    public static final String SUB_CATEGORY = "sub_category";
    public static final String LIKES = "likes";
    public static final String COLLECTS = "collects";
    public static final String COMMENTS = "comments";
    public static final String FOCUS = "focus";
}
