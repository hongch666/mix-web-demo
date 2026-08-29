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
        `password`,
        `email`,
        `role`,
        `img`
    )
VALUES (
        1001,
        'GLM',
        '******',
        'glm@example.com',
        'ai',
        'https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/glm.png'
    ),
    (
        1002,
        'Gemini',
        '******',
        'gemini@example.com',
        'ai',
        'https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/gemini.jpeg'
    ),
    (
        1003,
        'GPT',
        '******',
        'gpt@example.com',
        'ai',
        'https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/gpt.png'
    );
