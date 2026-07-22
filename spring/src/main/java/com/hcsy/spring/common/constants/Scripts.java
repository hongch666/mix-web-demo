package com.hcsy.spring.common.constants;

/**
 * 脚本类，统一管理数据库初始化 SQL
 */
public final class Scripts {

    private Scripts() {
    }

    public static final String INSERT_AI_USER = "INSERT IGNORE INTO user "
            + "(id, name, password, email, role, img, create_at, update_at) "
            + "VALUES (?, ?, ?, ?, 'ai', ?, NOW(), NOW())";

    public static final String CREATE_USER_TABLE = """
            CREATE TABLE IF NOT EXISTS user (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
                github_id BIGINT COMMENT 'GitHub用户ID',
                github_login VARCHAR(255) COMMENT 'GitHub登录名',
                github_url VARCHAR(255) COMMENT 'GitHub主页地址',
                name VARCHAR(255) NOT NULL UNIQUE COMMENT '用户名',
                password VARCHAR(255) NOT NULL COMMENT '密码',
                email VARCHAR(255) UNIQUE COMMENT '邮箱',
                age INT COMMENT '年龄',
                role VARCHAR(255) NOT NULL COMMENT '用户权限',
                img VARCHAR(255) COMMENT '用户头像',
                signature VARCHAR(255) COMMENT '个性签名',
                auth_provider VARCHAR(50) NOT NULL DEFAULT 'local' COMMENT '注册来源：local/github',
                last_login_at DATETIME COMMENT '最近登录时间',
                create_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                update_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY uk_user_github_id (github_id),
                INDEX idx_user_auth_provider (auth_provider)
            ) COMMENT='用户表'
            """;

    public static final String CREATE_ARTICLES_TABLE = """
            CREATE TABLE IF NOT EXISTS articles (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '文章id',
                title VARCHAR(255) NOT NULL COMMENT '文章标题',
                content LONGTEXT NOT NULL COMMENT '文章内容',
                user_id BIGINT NOT NULL COMMENT '用户id',
                sub_category_id BIGINT NOT NULL COMMENT '子分类id',
                tags VARCHAR(255) NOT NULL COMMENT '文章标签',
                status TINYINT NOT NULL COMMENT '文章状态',
                views INT NOT NULL COMMENT '文章浏览量',
                create_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                update_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
            ) COMMENT='文章表'
            """;

    public static final String CREATE_CATEGORY_TABLE = """
            CREATE TABLE IF NOT EXISTS category (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
                name VARCHAR(255) NOT NULL COMMENT '分类名称',
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
            ) COMMENT='分类表'
            """;

    public static final String CREATE_SUBCATEGORY_TABLE = """
            CREATE TABLE IF NOT EXISTS sub_category (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
                name VARCHAR(255) NOT NULL COMMENT '子分类名称',
                category_id BIGINT NOT NULL COMMENT '所属分类ID',
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE CASCADE
            ) COMMENT='子分类表'
            """;

    public static final String CREATE_CATEGORY_REFERENCE_TABLE = """
            CREATE TABLE IF NOT EXISTS category_reference (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
                sub_category_id BIGINT NOT NULL COMMENT '子分类ID',
                type VARCHAR(255) NOT NULL COMMENT '权威参考文本类型，link/pdf',
                link VARCHAR(255) COMMENT '权威参考文本链接',
                pdf VARCHAR(255) COMMENT '权威参考文本PDF链接（OSS）',
                UNIQUE KEY uk_sub_category (sub_category_id),
                FOREIGN KEY (sub_category_id) REFERENCES sub_category(id) ON DELETE CASCADE
            ) COMMENT='分类权威参考文本表'
            """;

    public static final String CREATE_COMMENTS_TABLE = """
            CREATE TABLE IF NOT EXISTS comments (
                id BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
                content TEXT COMMENT '评论内容',
                star DOUBLE COMMENT '星级评分，0~10',
                user_id BIGINT NOT NULL COMMENT '用户ID',
                article_id BIGINT NOT NULL COMMENT '文章ID',
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
            ) COMMENT='文章评论表'
            """;

    public static final String CREATE_LIKES_TABLE = """
            CREATE TABLE IF NOT EXISTS likes (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
                article_id BIGINT NOT NULL COMMENT '文章ID',
                user_id BIGINT NOT NULL COMMENT '用户ID',
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                UNIQUE KEY uk_article_user (article_id, user_id),
                KEY idx_user_id (user_id),
                KEY idx_created_time (created_time)
            ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '文章用户点赞表'
            """;

    public static final String CREATE_COLLECTS_TABLE = """
            CREATE TABLE IF NOT EXISTS collects (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
                article_id BIGINT NOT NULL COMMENT '文章ID',
                user_id BIGINT NOT NULL COMMENT '用户ID',
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                UNIQUE KEY uk_article_user (article_id, user_id),
                KEY idx_user_id (user_id),
                KEY idx_created_time (created_time)
            ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '文章用户收藏表'
            """;

    public static final String CREATE_FOCUS_TABLE = """
            CREATE TABLE IF NOT EXISTS focus (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
                user_id BIGINT NOT NULL COMMENT '用户ID',
                focus_id BIGINT NOT NULL COMMENT '关注的用户ID',
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                UNIQUE KEY uk_user_focus (user_id, focus_id),
                KEY idx_user_id (user_id),
                KEY idx_created_time (created_time)
            ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '关注表'
            """;
}
