-- API 日志 DWS 层：按日 + 接口聚合的轻度汇总
CREATE TABLE IF NOT EXISTS dws_api_day (
    action_date Date,
    api_path String,
    api_method String,
    api_description String,
    call_count Int64,
    total_response_time Float64,
    max_response_time Float64
) ENGINE = MergeTree
ORDER BY (
        action_date, api_path, api_method, api_description
    );
