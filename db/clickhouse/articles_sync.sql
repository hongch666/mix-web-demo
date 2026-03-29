-- 1. 创建映射库 (填入你的实际 MySQL 密码)
CREATE DATABASE demo ENGINE = MySQL (
    '127.0.0.1:3306',
    'demo',
    'root',
    '123456'
);

-- 2. 创建本地物理表 (对应你图片中的字段)
CREATE TABLE articles (
    id Int64,
    title String,
    content String,
    user_id Int64,
    sub_category_id Int64,
    tags String,
    status Int8,
    views Int32,
    create_at DateTime,
    update_at DateTime
) ENGINE = MergeTree ()
ORDER BY id;
-- 以 ID 排序，方便快速查找

-- 3. 创建物化视图，定期从 MySQL 同步数据到 ClickHouse
CREATE MATERIALIZED VIEW articles_sync_view REFRESH EVERY 10 SECOND -- 10 秒
TO default.articles AS
SELECT *
FROM demo.articles;
