CREATE TABLE IF NOT EXISTS `user` (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    github_id BIGINT COMMENT 'GitHub用户ID',
    github_login VARCHAR(255) COMMENT 'GitHub登录名',
    github_url VARCHAR(255) COMMENT 'GitHub主页地址',
    name VARCHAR(255) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码',
    email VARCHAR(255) UNIQUE COMMENT '邮箱',
    age INT COMMENT '年龄',
    role VARCHAR(255) NOT NULL COMMENT '用户权限',
    img VARCHAR(255) COMMENT '用户头像',
    signature VARCHAR(255) COMMENT '个性签名',
    auth_provider VARCHAR(50) NOT NULL DEFAULT 'local' COMMENT '注册来源：local/github',
    last_login_at DATETIME COMMENT '最近登录时间',
    create_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_user_github_id (github_id),
    INDEX idx_user_auth_provider (auth_provider)
) COMMENT = '用户表';

INSERT INTO
    `user` (
        `id`,
        `name`,
        `password`,
        `email`,
        `role`,
        `img`,
        `create_at`,
        `update_at`
    )
SELECT 1001, 'DeepSeek', '******', 'deepseek@example.com', 'ai', 'https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/deepseek.png', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
WHERE
    NOT EXISTS (
        SELECT 1
        FROM `user`
        WHERE
            `id` = 1001
    );

INSERT INTO
    `user` (
        `id`,
        `name`,
        `password`,
        `email`,
        `role`,
        `img`,
        `create_at`,
        `update_at`
    )
SELECT 1002, 'Gemini', '******', 'gemini@example.com', 'ai', 'https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/gemini.jpeg', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
WHERE
    NOT EXISTS (
        SELECT 1
        FROM `user`
        WHERE
            `id` = 1002
    );

INSERT INTO
    `user` (
        `id`,
        `name`,
        `password`,
        `email`,
        `role`,
        `img`,
        `create_at`,
        `update_at`
    )
SELECT 1003, 'GPT', '******', 'gpt@example.com', 'ai', 'https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/gpt.png', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
WHERE
    NOT EXISTS (
        SELECT 1
        FROM `user`
        WHERE
            `id` = 1003
    );
