-- API 日志 DWD 层：明细事件（补齐日期维度）
-- 排序键保持 event_id 作为 ReplacingMergeTree 去重键，接口路径用布隆索引加速过滤
CREATE TABLE IF NOT EXISTS dwd_api_call (
    event_id String,
    api_path String,
    api_method String,
    api_description String,
    user_id Int64,
    username String,
    response_time Float64,
    action_date Date,
    action_time DateTime,
    INDEX idx_api_path api_path TYPE bloom_filter(0.01) GRANULARITY 4
) ENGINE = ReplacingMergeTree (action_time)
PARTITION BY
    toYYYYMM (action_date)
ORDER BY event_id
TTL action_date + INTERVAL 24 MONTH;
