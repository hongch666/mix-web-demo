-- ODS 层：增量同步水位线表 sync_watermark
CREATE TABLE IF NOT EXISTS sync_watermark (
    table_name String,
    last_watermark String,
    updated_at DateTime
) ENGINE = ReplacingMergeTree (updated_at)
ORDER BY table_name;

INSERT INTO
    sync_watermark (
        table_name,
        last_watermark,
        updated_at
    )
SELECT table_name, '1970-01-01 00:00:00', now()
FROM (
        SELECT arrayJoin (
                [
                    'ods_articles', 'ods_user', 'ods_category', 'ods_sub_category', 'ods_likes', 'ods_collects', 'ods_comments', 'ods_focus', 'ods_article_log', 'ods_api_log'
                ]
            ) AS table_name
    )
WHERE
    table_name NOT IN (
        SELECT table_name
        FROM sync_watermark FINAL
    );
