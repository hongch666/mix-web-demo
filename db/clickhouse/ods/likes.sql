-- ODS 层：点赞明细表 ods_likes
CREATE TABLE IF NOT EXISTS ods_likes (
    id Int64,
    article_id Int64,
    user_id Int64,
    created_time DateTime
) ENGINE = ReplacingMergeTree (created_time)
ORDER BY id;
