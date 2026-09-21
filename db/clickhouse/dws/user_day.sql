-- DWS 层：用户日粒度行为汇总表 dws_user_day
CREATE TABLE IF NOT EXISTS dws_user_day (
    stat_date Date,
    user_id Int64,
    like_count Int64,
    collect_count Int64,
    comment_count Int64,
    focus_count Int64,
    liked_articles UInt64,
    last_active_time DateTime
) ENGINE = MergeTree
PARTITION BY
    toYYYYMM (stat_date)
ORDER BY (stat_date, user_id);
