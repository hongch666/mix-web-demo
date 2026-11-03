-- API 日志 ODS 层：NestJS MongoDB api_logs 按游标同步的原始事件
CREATE TABLE IF NOT EXISTS ods_api_log (
    event_id String,
    user_id Int64,
    username String,
    api_description String,
    api_path String,
    api_method String,
    response_time Float64,
    created_at DateTime,
    INDEX idx_api_path api_path TYPE bloom_filter(0.01) GRANULARITY 4
) ENGINE = ReplacingMergeTree (created_at)
PARTITION BY
    toYYYYMM (created_at)
ORDER BY (created_at, event_id)
TTL created_at + INTERVAL 24 MONTH;
