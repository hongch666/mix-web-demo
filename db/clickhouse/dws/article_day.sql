-- DWS 层：文章日粒度行为汇总表 dws_article_day
CREATE TABLE IF NOT EXISTS dws_article_day (
    stat_date Date,
    article_id Int64,
    user_id Int64,
    parent_category_id Int64,
    views Int64,
    like_count Int64,
    collect_count Int64,
    comment_count Int64,
    view_count Int64
) ENGINE = MergeTree
PARTITION BY
    toYYYYMM (stat_date)
ORDER BY (stat_date, article_id);
