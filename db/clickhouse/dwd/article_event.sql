-- DWD 层：文章事件明细表 dwd_article_event
CREATE TABLE IF NOT EXISTS dwd_article_event (
    id Int64,
    title String,
    user_id Int64,
    views Int32,
    status Int8,
    sub_category_id Int64,
    parent_category_id Int64,
    parent_category_name String,
    create_date Date,
    create_at DateTime,
    update_at DateTime
) ENGINE = ReplacingMergeTree (update_at)
ORDER BY id;
