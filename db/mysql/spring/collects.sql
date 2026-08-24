-- ============================================================
-- Spring 服务 - 收藏表
-- ============================================================

CREATE TABLE IF NOT EXISTS `collects` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `article_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_article_user` (`article_id`, `user_id`)
) COMMENT '文章收藏表';
