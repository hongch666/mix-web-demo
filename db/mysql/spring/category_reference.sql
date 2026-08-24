-- ============================================================
-- Spring 服务 - 分类权威文章关联表
-- ============================================================

CREATE TABLE IF NOT EXISTS `category_reference` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `sub_category_id` BIGINT NOT NULL,
    `type` VARCHAR(30),
    `link` VARCHAR(255),
    `pdf` VARCHAR(255),
    PRIMARY KEY (`id`),
    KEY `idx_sub_category_id` (`sub_category_id`)
) COMMENT '分类权威文章关联表';
