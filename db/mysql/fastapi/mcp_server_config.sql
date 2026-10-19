-- ============================================================
-- FastAPI 服务 - Agent MCP 服务配置表
-- ============================================================

CREATE TABLE IF NOT EXISTS `mcp_server_config` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `server_name` VARCHAR(64) NOT NULL COMMENT 'MCP 服务名，作为工具组标识与工具名前缀',
    `transport_type` VARCHAR(32) NOT NULL COMMENT '传输类型: stdio/sse/streamable_http',
    `command` VARCHAR(255) DEFAULT NULL COMMENT 'stdio 传输的可执行命令',
    `args_json` JSON DEFAULT NULL COMMENT 'stdio 传输的命令参数数组',
    `url` VARCHAR(255) DEFAULT NULL COMMENT 'sse/streamable_http 传输的服务地址',
    `env_json` JSON DEFAULT NULL COMMENT 'stdio 传输的环境变量',
    `headers_json` JSON DEFAULT NULL COMMENT 'sse/streamable_http 传输的请求头',
    `description` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '服务描述，用于运维辨识',
    `enabled` TINYINT NOT NULL DEFAULT 1 COMMENT '是否启用: 1 启用, 0 停用',
    `created_at` DATETIME,
    `updated_at` DATETIME,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_mcp_server_config_name` (`server_name`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = 'Agent MCP 服务配置表';
