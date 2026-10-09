-- ============================================================
-- FastAPI 服务 - 用户级聊天记忆摘要表
-- ============================================================

CREATE TABLE IF NOT EXISTS `ai_user_summary` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `summary` TEXT NOT NULL,
    `last_summarized_history_id` BIGINT NOT NULL DEFAULT 0,
    `summarized_count` INT NOT NULL DEFAULT 0,
    `created_at` DATETIME,
    `updated_at` DATETIME,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_ai_user_summary_user_id` (`user_id`),
    KEY `ix_ai_user_summary_id` (`id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '用户级聊天记忆摘要表';
