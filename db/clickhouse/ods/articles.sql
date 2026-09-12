-- ODS 层：文章明细表 ods_articles
CREATE TABLE IF NOT EXISTS ods_articles (
    id Int64,
    title String,
    user_id Int64,
    sub_category_id Int64,
    tags String,
    status Int8,
    views Int32,
    create_at DateTime,
    update_at DateTime
) ENGINE = ReplacingMergeTree (update_at)
ORDER BY id;
