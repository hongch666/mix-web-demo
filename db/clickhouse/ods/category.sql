-- ODS 层：分类明细表 ods_category
CREATE TABLE IF NOT EXISTS ods_category (
    id Int64,
    name String,
    create_time DateTime,
    update_time DateTime
) ENGINE = ReplacingMergeTree (update_time)
ORDER BY id;
