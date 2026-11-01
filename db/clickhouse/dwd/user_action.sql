-- DWD 层：用户行为明细表 dwd_user_action
-- 排序键保持 event_id 作为 ReplacingMergeTree 去重键，查询过滤列用跳数索引加速
CREATE TABLE IF NOT EXISTS dwd_user_action (
    event_id String,
    source_type String,
    source_id Int64,
    action_type String,
    user_id Int64,
    article_id Int64,
    action_date Date,
    action_time DateTime,
    INDEX idx_action_type action_type TYPE set(64) GRANULARITY 4,
    INDEX idx_user_id user_id TYPE minmax GRANULARITY 4,
    INDEX idx_article_id article_id TYPE minmax GRANULARITY 4
) ENGINE = ReplacingMergeTree (action_time)
PARTITION BY
    toYYYYMM (action_date)
ORDER BY event_id
TTL action_date + INTERVAL 24 MONTH;
