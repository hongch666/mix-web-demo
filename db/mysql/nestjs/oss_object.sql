-- ============================================================
-- NestJS 服务 - OSS对象账本表
-- ============================================================

CREATE TABLE IF NOT EXISTS `oss_object` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '账本ID',
    `oss_key` VARCHAR(512) NOT NULL COMMENT 'OSS 对象 key（不含域名）',
    `oss_url` VARCHAR(1024) NOT NULL COMMENT 'OSS 对象完整访问 URL',
    `prefix_type` VARCHAR(32) NOT NULL COMMENT 'key 前缀类型',
    `source` VARCHAR(32) NOT NULL COMMENT '上传来源',
    `uploader_user_id` BIGINT COMMENT '上传用户ID，匿名上传为空',
    `file_size` BIGINT COMMENT '对象字节数',
    `last_verified_at` DATETIME COMMENT '最近一次扫描确认在用的时间',
    `create_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_oss_object_key` (`oss_key`),
    KEY `idx_oss_object_created_at` (`create_at`),
    KEY `idx_oss_object_prefix_type` (`prefix_type`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = 'OSS对象账本表';
