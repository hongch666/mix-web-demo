-- API 日志 ADS 层：接口平均响应速度（与远程聚合结果同构，供分析接口直接查询）
CREATE TABLE IF NOT EXISTS ads_api_average_speed (
    api_path String,
    api_method String,
    api_description String,
    avg_response_time Float64,
    call_count Int64,
    stat_time DateTime
) ENGINE = ReplacingMergeTree (stat_time)
ORDER BY (
        api_path, api_method, api_description
    );
