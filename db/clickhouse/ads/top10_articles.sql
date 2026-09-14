-- ADS 层：阅读量最高的文章榜单表 ads_top10_articles
CREATE TABLE IF NOT EXISTS ads_top10_articles (
    id Int64,
    title String,
    tags String,
    status Int8,
    views Int32,
    create_at DateTime,
    update_at DateTime,
    user_id Int64,
    user_name String,
    sub_category_id Int64,
    stat_time DateTime
) ENGINE = ReplacingMergeTree (stat_time)
ORDER BY id;
