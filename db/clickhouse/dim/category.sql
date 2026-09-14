-- DIM 层：分类维度表 dim_category，子分类与父分类扁平化合并
CREATE TABLE IF NOT EXISTS dim_category (
    sub_category_id Int64,
    sub_category_name String,
    parent_category_id Int64,
    parent_category_name String,
    update_time DateTime
) ENGINE = ReplacingMergeTree (update_time)
ORDER BY sub_category_id;
