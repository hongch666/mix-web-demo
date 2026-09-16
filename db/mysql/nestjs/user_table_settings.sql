-- ============================================================
-- NestJS 服务 - 用户表设置表
-- ============================================================

CREATE TABLE IF NOT EXISTS `user_table_settings` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '设置ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `table_key` VARCHAR(64) NOT NULL COMMENT '页面标识',
    `columns` JSON NOT NULL COMMENT '列配置JSON',
    `create_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_table` (`user_id`, `table_key`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '用户表设置表';
