-- 用户分析 ADS 层：按用户聚合的累计指标（含作为作者的获赞获藏与作为观众的浏览分布）
CREATE TABLE IF NOT EXISTS ads_user_stats (
    user_id Int64,
    total_likes_given Int64,
    total_collects_given Int64,
    total_comments Int64,
    total_focus Int64,
    total_views_given Int64,
    total_articles Int64,
    total_views_received Int64,
    total_likes_received Int64,
    total_collects_received Int64,
    total_followers Int64,
    last_active_time DateTime,
    stat_time DateTime
) ENGINE = ReplacingMergeTree (stat_time)
ORDER BY user_id;
