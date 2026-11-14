-- 搜索关键词 ADS 层：从文章日志中按关键词去重并统计搜索次数，供 FastAPI 词云接口按热度查询
CREATE TABLE IF NOT EXISTS ads_search_keywords (
    keyword String,
    search_count UInt64,
    stat_time DateTime
) ENGINE = ReplacingMergeTree (stat_time)
ORDER BY keyword;
