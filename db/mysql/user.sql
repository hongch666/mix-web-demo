CREATE TABLE IF NOT EXISTS `user` (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    name VARCHAR(255) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码',
    email VARCHAR(255) UNIQUE COMMENT '邮箱',
    age INT COMMENT '年龄',
    role VARCHAR(255) NOT NULL COMMENT '用户权限',
    img VARCHAR(255) COMMENT '用户头像',
    signature VARCHAR(255) COMMENT '个性签名'
) COMMENT='用户表';

INSERT INTO `user` (`id`, `name`, `password`, `email`, `role`, `img`)
SELECT 1001, '豆包', '******', 'doubao@example.com', 'ai', 'https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/%E8%B1%86%E5%8C%85.jpeg'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `id` = 1001);

INSERT INTO `user` (`id`, `name`, `password`, `email`, `role`, `img`)
SELECT 1002, 'Gemini', '******', 'gemini@example.com', 'ai', 'https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/gemini.jpeg'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `id` = 1002);

INSERT INTO `user` (`id`, `name`, `password`, `email`, `role`, `img`)
SELECT 1003, 'Qwen', '******', 'qwen@example.com', 'ai', 'https://mix-web-demo.oss-cn-guangzhou.aliyuncs.com/pic/%E9%80%9A%E4%B9%89%E5%8D%83%E9%97%AE.jpeg'
WHERE NOT EXISTS (SELECT 1 FROM `user` WHERE `id` = 1003);
