-- ADS 层：父分类文章数量统计表 ads_category_stats
CREATE TABLE IF NOT EXISTS ads_category_stats (
    parent_category_id Int64,
    category_name String,
    article_count Int64,
    stat_time DateTime
) ENGINE = ReplacingMergeTree (stat_time)
ORDER BY parent_category_id;
