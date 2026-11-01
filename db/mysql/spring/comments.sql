-- ============================================================
-- Spring 服务 - 文章评论表
-- ============================================================

CREATE TABLE IF NOT EXISTS `comments` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `content` TEXT COMMENT '评论内容',
    `star` DOUBLE COMMENT '星级评分，0~10',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `article_id` BIGINT NOT NULL COMMENT '文章ID',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_create_time` (`user_id`, `create_time`),
    KEY `idx_article_star` (`article_id`, `star`),
    KEY `idx_update_time_id` (`update_time`, `id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '文章评论表';
