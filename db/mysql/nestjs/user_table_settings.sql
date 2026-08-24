-- ============================================================
-- NestJS 服务 - 用户表设置表
-- ============================================================

CREATE TABLE IF NOT EXISTS `user_table_settings` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `table_key` VARCHAR(64) NOT NULL,
    `columns` JSON NOT NULL,
    `create_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_table` (`user_id`, `table_key`)
) COMMENT '用户表设置表';
