CREATE TABLE IF NOT EXISTS focus (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    focus_id BIGINT NOT NULL COMMENT '关注的用户ID',
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_user_focus (user_id, focus_id),
    KEY idx_user_id (user_id),
    KEY idx_created_time (created_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '关注表';
