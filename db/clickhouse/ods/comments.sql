-- ODS 层：评论明细表 ods_comments
CREATE TABLE IF NOT EXISTS ods_comments (
    id Int64,
    user_id Int64,
    article_id Int64,
    star Float64,
    create_time DateTime,
    update_time DateTime
) ENGINE = ReplacingMergeTree (update_time)
ORDER BY id;
