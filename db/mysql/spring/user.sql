-- ============================================================
-- Spring 服务 - 用户表
-- ============================================================

CREATE TABLE IF NOT EXISTS `user` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `github_id` BIGINT COMMENT 'GitHub用户ID',
    `github_login` VARCHAR(255) COMMENT 'GitHub登录名',
    `github_url` VARCHAR(255) COMMENT 'GitHub主页地址',
    `name` VARCHAR(255) NOT NULL COMMENT '用户名',
    `password` VARCHAR(255) COMMENT '密码',
    `email` VARCHAR(255) COMMENT '邮箱',
    `age` INT COMMENT '年龄',
    `role` VARCHAR(255) NOT NULL COMMENT '用户权限',
    `img` VARCHAR(255) COMMENT '用户头像',
    `signature` VARCHAR(255) COMMENT '个性签名',
    `auth_provider` VARCHAR(50) NOT NULL DEFAULT 'local' COMMENT '注册来源：local/github',
    `last_login_at` DATETIME COMMENT '最近登录时间',
    `create_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_name` (`name`),
    UNIQUE KEY `uk_email` (`email`),
    UNIQUE KEY `uk_user_github_id` (`github_id`),
    INDEX `idx_user_auth_provider` (`auth_provider`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户表';

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
