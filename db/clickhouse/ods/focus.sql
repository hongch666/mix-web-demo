-- ODS 层：关注明细表 ods_focus
CREATE TABLE IF NOT EXISTS ods_focus (
    id Int64,
    user_id Int64,
    focus_id Int64,
    created_time DateTime
) ENGINE = ReplacingMergeTree (created_time)
ORDER BY id;
