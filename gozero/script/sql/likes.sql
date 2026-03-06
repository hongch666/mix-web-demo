CREATE TABLE IF NOT EXISTS likes (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
    article_id BIGINT NOT NULL COMMENT '文章ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_article_user (article_id, user_id),
    KEY idx_user_id (user_id),
    KEY idx_created_time (created_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '文章用户点赞表';