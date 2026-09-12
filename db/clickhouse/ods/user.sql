-- ODS 层：用户明细表 ods_user
CREATE TABLE IF NOT EXISTS ods_user (
    id Int64,
    name String,
    role String,
    img String,
    signature String,
    create_at DateTime,
    update_at DateTime
) ENGINE = ReplacingMergeTree (update_at)
ORDER BY id;
