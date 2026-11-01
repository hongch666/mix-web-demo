-- ODS 层：文章行为日志表 ods_article_log，来源于 NestJS MongoDB article_logs
CREATE TABLE IF NOT EXISTS ods_article_log (
    event_id String,
    user_id Int64,
    article_id Int64,
    action String,
    content String,
    created_at DateTime,
    INDEX idx_action action TYPE set(64) GRANULARITY 4,
    INDEX idx_created_at created_at TYPE minmax GRANULARITY 4
) ENGINE = ReplacingMergeTree (created_at)
PARTITION BY
    toYYYYMM (created_at)
ORDER BY (created_at, event_id)
TTL created_at + INTERVAL 24 MONTH;
