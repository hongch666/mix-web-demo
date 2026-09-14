-- API 日志 ADS 层：接口调用次数（与远程聚合结果同构，供分析接口直接查询）
CREATE TABLE IF NOT EXISTS ads_api_called_count (
    api_path String,
    api_method String,
    api_description String,
    call_count Int64,
    avg_response_time Float64,
    stat_time DateTime
) ENGINE = ReplacingMergeTree (stat_time)
ORDER BY (
        api_path, api_method, api_description
    );
