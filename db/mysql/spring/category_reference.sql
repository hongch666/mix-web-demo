-- ============================================================
-- Spring 服务 - 分类权威参考文本表
-- ============================================================

CREATE TABLE IF NOT EXISTS `category_reference` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `sub_category_id` BIGINT NOT NULL COMMENT '子分类ID',
    `type` VARCHAR(255) NOT NULL COMMENT '权威参考文本类型，link/pdf',
    `link` VARCHAR(255) COMMENT '权威参考文本链接',
    `pdf` VARCHAR(255) COMMENT '权威参考文本PDF链接（OSS）',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_sub_category` (`sub_category_id`),
    CONSTRAINT `fk_category_reference_sub_category` FOREIGN KEY (`sub_category_id`) REFERENCES `sub_category` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '分类权威参考文本表';
