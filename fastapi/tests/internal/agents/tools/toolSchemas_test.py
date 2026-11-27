import pytest
from pydantic import ValidationError

from app.core.constants import Defaults, WarehouseScripts
from app.internal.agents.tools.toolSchemas import (
    MongoAggregateInput,
    MongoQueryInput,
    SqlQueryInput,
    build_predefined_query_input,
    build_warehouse_query_input,
)


# SQL 参数被整体写成 JSON 字符串时还原为键值对象
def test_sql_query_input_parses_json_string_params() -> None:
    schema = SqlQueryInput(query="SELECT id FROM t LIMIT 1", params='{"id": 1}')

    assert schema.params == {"id": 1}


# MongoDB 查询工具的上限在入参校验阶段就拒绝超限值
def test_mongo_query_input_rejects_limit_over_remote_max() -> None:
    MongoQueryInput(
        collection_name="apilogs",
        filter_dict={},
        limit=Defaults.MONGODB_QUERY_MAX_LIMIT,
    )

    with pytest.raises(ValidationError):
        MongoQueryInput(
            collection_name="apilogs",
            filter_dict={},
            limit=Defaults.MONGODB_QUERY_MAX_LIMIT + 1,
        )


# MongoDB 聚合工具的上限与远程服务阈值一致
def test_mongo_aggregate_input_rejects_limit_over_remote_max() -> None:
    pipeline = [{"$count": "total"}]
    MongoAggregateInput(
        collection_name="apilogs",
        pipeline=pipeline,
        limit=Defaults.MONGODB_AGGREGATE_MAX_DOCS,
    )

    with pytest.raises(ValidationError):
        MongoAggregateInput(
            collection_name="apilogs",
            pipeline=pipeline,
            limit=Defaults.MONGODB_AGGREGATE_MAX_DOCS + 1,
        )


# 图谱查询的可选值来自当前可用的预定义查询名
def test_predefined_query_input_lists_available_names() -> None:
    schema = build_predefined_query_input(["article_by_id", "user_by_id"])

    description = schema.model_json_schema()["properties"]["query_name"]["description"]
    assert description == "预定义查询名称，可选值: article_by_id, user_by_id"


# 数仓数据集说明与工具支持的数据集清单保持一致
def test_warehouse_query_input_lists_agent_datasets() -> None:
    schema = build_warehouse_query_input()

    description = schema.model_json_schema()["properties"]["dataset"]["description"]
    assert description.startswith("ADS 数据集名称")
    for dataset in WarehouseScripts.WAREHOUSE_AGENT_DATASETS:
        assert dataset in description
