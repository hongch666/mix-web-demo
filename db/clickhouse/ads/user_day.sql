-- 用户分析 ADS 层：按用户聚合的日粒度行为汇总，供用户分析接口直接查询
CREATE TABLE IF NOT EXISTS ads_user_day (
    stat_date Date,
    user_id Int64,
    like_count Int64,
    collect_count Int64,
    comment_count Int64,
    focus_count Int64,
    view_count Int64,
    last_active_time DateTime,
    stat_time DateTime
) ENGINE = ReplacingMergeTree (stat_time)
ORDER BY (stat_date, user_id);
