-- DIM 层：用户维度表 dim_user
CREATE TABLE IF NOT EXISTS dim_user (
    id Int64,
    name String,
    role String,
    img String,
    signature String,
    create_at DateTime,
    update_at DateTime
) ENGINE = ReplacingMergeTree (update_at)
ORDER BY id;
