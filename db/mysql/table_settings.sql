-- 用户表格列设置表 -- 存储用户在不同页面的表格列配置（显隐、顺序、宽度等）

CREATE TABLE IF NOT EXISTS `user_table_settings` (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '设置ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    table_key VARCHAR(64) NOT NULL COMMENT '页面标识，如 articles/users/comments',
    columns JSON NOT NULL COMMENT '列配置JSON，存储列的显隐/顺序/宽度',
    create_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_user_table (user_id, table_key),
    INDEX idx_user_table_settings_user_id (user_id)
) COMMENT = '用户表格列设置';
