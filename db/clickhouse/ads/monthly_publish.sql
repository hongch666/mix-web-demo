-- ADS 层：月度文章发布趋势表 ads_monthly_publish
CREATE TABLE IF NOT EXISTS ads_monthly_publish (
    year_month String,
    article_count Int64,
    stat_time DateTime
) ENGINE = ReplacingMergeTree (stat_time)
ORDER BY year_month;
