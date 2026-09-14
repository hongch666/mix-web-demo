-- DWD 层：用户行为明细表 dwd_user_action
CREATE TABLE IF NOT EXISTS dwd_user_action (
    event_id String,
    source_type String,
    source_id Int64,
    action_type String,
    user_id Int64,
    article_id Int64,
    action_date Date,
    action_time DateTime
) ENGINE = ReplacingMergeTree (action_time)
ORDER BY event_id;
