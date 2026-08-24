-- ============================================================
-- Spring 服务 - 关注表
-- ============================================================

CREATE TABLE IF NOT EXISTS `focus` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `focus_id` BIGINT NOT NULL,
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_focus` (`user_id`, `focus_id`)
) COMMENT '用户关注表';
