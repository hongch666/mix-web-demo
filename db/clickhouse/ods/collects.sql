-- ODS 层：收藏明细表 ods_collects
CREATE TABLE IF NOT EXISTS ods_collects (
    id Int64,
    article_id Int64,
    user_id Int64,
    created_time DateTime
) ENGINE = ReplacingMergeTree (created_time)
ORDER BY id;
