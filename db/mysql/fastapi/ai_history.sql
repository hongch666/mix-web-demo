-- ============================================================
-- FastAPI 服务 - AI聊天记录表
-- ============================================================

CREATE TABLE IF NOT EXISTS `ai_history` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT,
    `ask` TEXT NOT NULL,
    `reply` TEXT NOT NULL,
    `thinking` TEXT,
    `ai_type` VARCHAR(50) NOT NULL,
    `created_at` DATETIME,
    `updated_at` DATETIME,
    PRIMARY KEY (`id`),
    KEY `ix_ai_history_id` (`id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = 'AI聊天记录表';
