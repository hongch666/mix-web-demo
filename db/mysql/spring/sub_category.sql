-- ============================================================
-- Spring 服务 - 子分类表
-- ============================================================

CREATE TABLE IF NOT EXISTS `sub_category` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `category_id` BIGINT NOT NULL,
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_category_id` (`category_id`),
    FOREIGN KEY (`category_id`) REFERENCES `category` (`id`) ON DELETE CASCADE
) COMMENT '文章子分类表';
