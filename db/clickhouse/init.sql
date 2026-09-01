-- ClickHouse 数仓初始化脚本
-- MySQL 是业务主库，ClickHouse 只保存分析所需字段和汇总结果。

CREATE DATABASE IF NOT EXISTS warehouse;

CREATE TABLE IF NOT EXISTS warehouse.sync_watermark (
    table_name String,
    last_watermark String,
    updated_at DateTime
) ENGINE = ReplacingMergeTree (updated_at)
ORDER BY table_name;

CREATE TABLE IF NOT EXISTS warehouse.ods_articles (
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

CREATE TABLE IF NOT EXISTS warehouse.ods_user (
    id Int64,
    name String,
    role String,
    img String,
    signature String,
    create_at DateTime,
    update_at DateTime
) ENGINE = ReplacingMergeTree (update_at)
ORDER BY id;

CREATE TABLE IF NOT EXISTS warehouse.ods_category (
    id Int64,
    name String,
    create_time DateTime,
    update_time DateTime
) ENGINE = ReplacingMergeTree (update_time)
ORDER BY id;

CREATE TABLE IF NOT EXISTS warehouse.ods_sub_category (
    id Int64,
    name String,
    category_id Int64,
    create_time DateTime,
    update_time DateTime
) ENGINE = ReplacingMergeTree (update_time)
ORDER BY id;

CREATE TABLE IF NOT EXISTS warehouse.ods_likes (
    id Int64,
    article_id Int64,
    user_id Int64,
    created_time DateTime
) ENGINE = ReplacingMergeTree (created_time)
ORDER BY id;

CREATE TABLE IF NOT EXISTS warehouse.ods_collects (
    id Int64,
    article_id Int64,
    user_id Int64,
    created_time DateTime
) ENGINE = ReplacingMergeTree (created_time)
ORDER BY id;

CREATE TABLE IF NOT EXISTS warehouse.ods_comments (
    id Int64,
    user_id Int64,
    article_id Int64,
    star Float64,
    create_time DateTime,
    update_time DateTime
) ENGINE = ReplacingMergeTree (update_time)
ORDER BY id;

CREATE TABLE IF NOT EXISTS warehouse.ods_focus (
    id Int64,
    user_id Int64,
    focus_id Int64,
    created_time DateTime
) ENGINE = ReplacingMergeTree (created_time)
ORDER BY id;

CREATE TABLE IF NOT EXISTS warehouse.ods_article_log (
    event_id String,
    user_id Int64,
    article_id Int64,
    action String,
    content String,
    created_at DateTime
) ENGINE = ReplacingMergeTree (created_at)
ORDER BY event_id;

CREATE TABLE IF NOT EXISTS warehouse.dim_user (
    id Int64,
    name String,
    role String,
    img String,
    signature String,
    create_at DateTime,
    update_at DateTime
) ENGINE = ReplacingMergeTree (update_at)
ORDER BY id;

CREATE TABLE IF NOT EXISTS warehouse.dim_category (
    sub_category_id Int64,
    sub_category_name String,
    parent_category_id Int64,
    parent_category_name String,
    update_time DateTime
) ENGINE = ReplacingMergeTree (update_time)
ORDER BY sub_category_id;

CREATE TABLE IF NOT EXISTS warehouse.dwd_article_event (
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

CREATE TABLE IF NOT EXISTS warehouse.dwd_user_action (
    event_id String,
    source_type String,
    source_id Int64,
    action_type String,
    user_id Int64,
    article_id Int64,
    action_date Date,
    action_time DateTime
) ENGINE = ReplacingMergeTree (action_time)
ORDER BY event_id;

CREATE TABLE IF NOT EXISTS warehouse.dws_article_day (
    stat_date Date,
    article_id Int64,
    user_id Int64,
    parent_category_id Int64,
    views Int64,
    like_count Int64,
    collect_count Int64,
    comment_count Int64,
    view_count Int64
) ENGINE = MergeTree
ORDER BY (stat_date, article_id);

CREATE TABLE IF NOT EXISTS warehouse.dws_user_day (
    stat_date Date,
    user_id Int64,
    like_count Int64,
    collect_count Int64,
    comment_count Int64,
    focus_count Int64,
    liked_articles UInt64,
    last_active_time DateTime
) ENGINE = MergeTree
ORDER BY (stat_date, user_id);

CREATE TABLE IF NOT EXISTS warehouse.ads_top10_articles (
    id Int64,
    title String,
    tags String,
    status Int8,
    views Int32,
    create_at DateTime,
    update_at DateTime,
    user_id Int64,
    sub_category_id Int64,
    stat_time DateTime
) ENGINE = ReplacingMergeTree (stat_time)
ORDER BY id;

CREATE TABLE IF NOT EXISTS warehouse.ads_category_stats (
    parent_category_id Int64,
    category_name String,
    article_count Int64,
    stat_time DateTime
) ENGINE = ReplacingMergeTree (stat_time)
ORDER BY parent_category_id;

CREATE TABLE IF NOT EXISTS warehouse.ads_monthly_publish (
    year_month String,
    article_count Int64,
    stat_time DateTime
) ENGINE = ReplacingMergeTree (stat_time)
ORDER BY year_month;

CREATE TABLE IF NOT EXISTS warehouse.ads_platform_stats (
    id UInt8,
    stat_time DateTime,
    total_views Int64,
    total_articles Int64,
    active_authors UInt64,
    average_views Float64,
    total_likes Int64,
    average_likes Float64,
    total_collects Int64,
    average_collects Float64
) ENGINE = ReplacingMergeTree (stat_time)
ORDER BY id;

CREATE TABLE IF NOT EXISTS warehouse.ads_user_profile (
    user_id Int64,
    user_name String,
    total_likes_given Int64,
    total_collects_given Int64,
    total_comments Int64,
    total_focus Int64,
    total_articles Int64,
    total_views Int64,
    last_active_time DateTime,
    stat_time DateTime
) ENGINE = ReplacingMergeTree (stat_time)
ORDER BY user_id;

INSERT INTO warehouse.sync_watermark (table_name, last_watermark, updated_at)
SELECT table_name, '1970-01-01 00:00:00', now()
FROM (SELECT arrayJoin([
    'ods_articles', 'ods_user', 'ods_category', 'ods_sub_category',
    'ods_likes', 'ods_collects', 'ods_comments', 'ods_focus', 'ods_article_log'
]) AS table_name)
WHERE table_name NOT IN (SELECT table_name FROM warehouse.sync_watermark FINAL);
