-- ============================================================
-- GoZero 服务 - 聊天消息表
-- ============================================================

CREATE TABLE IF NOT EXISTS `chat_messages` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '消息ID，主键',
    `sender_id` BIGINT NOT NULL COMMENT '发送者ID',
    `receiver_id` BIGINT NOT NULL COMMENT '接收者ID',
    `content` TEXT NOT NULL COMMENT '消息内容',
    `is_read` TINYINT NOT NULL DEFAULT 0 COMMENT '是否已读，0未读，1已读',
    `created_at` DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
    `conversation_low` BIGINT GENERATED ALWAYS AS (LEAST(`sender_id`, `receiver_id`)) VIRTUAL COMMENT '会话对端较小ID',
    `conversation_high` BIGINT GENERATED ALWAYS AS (GREATEST(`sender_id`, `receiver_id`)) VIRTUAL COMMENT '会话对端较大ID',
    PRIMARY KEY (`id`),
    KEY `idx_conversation_created` (`conversation_low`, `conversation_high`, `created_at`, `id`),
    KEY `idx_receiver_unread` (`receiver_id`, `is_read`, `sender_id`),
    KEY `idx_receiver_sender_read` (`receiver_id`, `sender_id`, `is_read`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '聊天消息表';
