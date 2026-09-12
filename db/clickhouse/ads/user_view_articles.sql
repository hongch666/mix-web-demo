-- 用户分析 ADS 层：用户浏览过的文章分布（预聚合，消除查询期 JOIN）
CREATE TABLE IF NOT EXISTS ads_user_view_articles (
    user_id Int64,
    article_id Int64,
    article_title String,
    view_count Int64,
    stat_time DateTime
) ENGINE = ReplacingMergeTree (stat_time)
ORDER BY (user_id, article_id);
