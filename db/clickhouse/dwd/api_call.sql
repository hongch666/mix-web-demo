-- API 日志 DWD 层：明细事件（补齐日期维度）
CREATE TABLE IF NOT EXISTS dwd_api_call (
    event_id String,
    api_path String,
    api_method String,
    api_description String,
    user_id Int64,
    username String,
    response_time Float64,
    action_date Date,
    action_time DateTime
) ENGINE = ReplacingMergeTree (action_time)
ORDER BY event_id;
