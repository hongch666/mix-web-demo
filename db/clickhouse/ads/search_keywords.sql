-- 搜索关键词 ADS 层：从文章日志中提取并去重，供 FastAPI 词云接口查询
CREATE TABLE IF NOT EXISTS ads_search_keywords (
    keyword String,
    stat_time DateTime
) ENGINE = ReplacingMergeTree (stat_time)
ORDER BY keyword;
