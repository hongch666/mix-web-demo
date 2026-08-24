-- ============================================================
-- Spring 服务 - 用户表
-- ============================================================

CREATE TABLE IF NOT EXISTS `user` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `github_id` BIGINT,
    `github_login` VARCHAR(255),
    `github_url` VARCHAR(255),
    `name` VARCHAR(255) NOT NULL,
    `password` VARCHAR(255),
    `age` INT,
    `email` VARCHAR(255),
    `role` VARCHAR(30) DEFAULT 'user',
    `img` VARCHAR(255),
    `signature` TEXT,
    `auth_provider` VARCHAR(30),
    `last_login_at` DATETIME,
    `create_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_github_id` (`github_id`),
    UNIQUE KEY `uk_name` (`name`),
    UNIQUE KEY `uk_email` (`email`)
) COMMENT '用户表';

-- AI 用户初始化数据
INSERT IGNORE INTO
    `user` (
        `id`,
        `name`,
        `role`,
        `img`,
        `signature`
    )
VALUES (
        1001,
        '豆包AI',
        'ai',
        '/pic/ai/doubao.png',
        '字节跳动豆包大模型'
    ),
    (
        1002,
        '通义千问',
        'ai',
        '/pic/ai/qwen.png',
        '阿里云通义千问大模型'
    ),
    (
        1003,
        'Gemini',
        'ai',
        '/pic/ai/gemini.png',
        'Google Gemini 大模型'
    );
