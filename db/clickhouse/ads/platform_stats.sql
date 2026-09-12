-- ADS 层：平台整体统计表 ads_platform_stats
CREATE TABLE IF NOT EXISTS ads_platform_stats (
    id UInt8,
    stat_time DateTime,
    total_views Int64,
    total_articles Int64,
    active_authors UInt64,
    average_views Float64,
    total_likes Int64,
    average_likes Float64,
    total_collects Int64,
    average_collects Float64
) ENGINE = ReplacingMergeTree (stat_time)
ORDER BY id;
