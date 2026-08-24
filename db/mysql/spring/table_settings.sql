-- ============================================================
-- Spring 服务 - 表配置表
-- ============================================================

CREATE TABLE IF NOT EXISTS `table_settings` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `table_name` VARCHAR(255) NOT NULL,
    `settings` JSON,
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_table_name` (`table_name`)
) COMMENT '表配置表';
