-- ODS 层：文章行为日志表 ods_article_log，来源于 NestJS MongoDB article_logs
CREATE TABLE IF NOT EXISTS ods_article_log (
    event_id String,
    user_id Int64,
    article_id Int64,
    action String,
    content String,
    created_at DateTime
) ENGINE = ReplacingMergeTree (created_at)
ORDER BY event_id;
