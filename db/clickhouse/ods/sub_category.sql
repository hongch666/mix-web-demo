-- ODS 层：子分类明细表 ods_sub_category
CREATE TABLE IF NOT EXISTS ods_sub_category (
    id Int64,
    name String,
    category_id Int64,
    create_time DateTime,
    update_time DateTime
) ENGINE = ReplacingMergeTree (update_time)
ORDER BY id;
