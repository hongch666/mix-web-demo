-- ============================================================
-- Spring 服务 - 文章表
-- ============================================================

CREATE TABLE IF NOT EXISTS `articles` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `title` VARCHAR(255) NOT NULL,
    `content` TEXT NOT NULL,
    `tags` VARCHAR(255),
    `user_id` BIGINT NOT NULL,
    `sub_category_id` BIGINT NOT NULL,
    `status` TINYINT DEFAULT 1,
    `views` INT DEFAULT 0,
    `create_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_sub_category_id` (`sub_category_id`),
    KEY `idx_status` (`status`)
) COMMENT '文章表';
