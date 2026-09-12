-- API 日志 ODS 层：NestJS MongoDB api_logs 按游标同步的原始事件
CREATE TABLE IF NOT EXISTS ods_api_log (
    event_id String,
    user_id Int64,
    username String,
    api_description String,
    api_path String,
    api_method String,
    response_time Float64,
    created_at DateTime
) ENGINE = ReplacingMergeTree (created_at)
ORDER BY event_id;
