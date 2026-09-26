"""ClickHouseWarehouseTools 数仓查询工具的单元测试"""

import json
from unittest.mock import AsyncMock

import pytest

from app.core.constants import Messages, WarehouseScripts
from app.internal.agents.tools import warehouseTools as warehouse_module
from app.internal.agents.tools.warehouseTools import ClickHouseWarehouseTools


# 列出数据集返回配置的数据集描述
@pytest.mark.anyio
async def test_list_datasets_returns_configured_descriptions() -> None:
    result = json.loads(await ClickHouseWarehouseTools().list_datasets())

    assert result == WarehouseScripts.WAREHOUSE_AGENT_DATASET_DESCRIPTIONS


# 不支持的数据集返回不支持消息
@pytest.mark.anyio
async def test_query_rejects_unsupported_dataset() -> None:
    result = await ClickHouseWarehouseTools().query_warehouse("not_exists")

    assert result == Messages.WAREHOUSE_DATASET_UNSUPPORTED.format(dataset="not_exists")


# user_profile 数据集缺少 user_id 时返回必填提示
@pytest.mark.anyio
async def test_query_requires_user_id_for_user_dataset() -> None:
    result = await ClickHouseWarehouseTools().query_warehouse("user_profile")

    assert result == Messages.WAREHOUSE_USER_ID_REQUIRED


# 非法日期格式返回日期无效消息
@pytest.mark.anyio
async def test_query_rejects_invalid_date() -> None:
    tool = ClickHouseWarehouseTools()

    result = await tool.query_warehouse("platform_stats", start_date="2026/01/01")

    assert result == Messages.WAREHOUSE_DATE_INVALID


# limit 上限收敛为 100 且日期缺省补默认区间
@pytest.mark.anyio
async def test_query_clamps_limit_and_applies_date_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    execute = AsyncMock(return_value=[(1, 2)])
    monkeypatch.setattr(warehouse_module, "execute_clickhouse_query", execute)

    result = await ClickHouseWarehouseTools().query_warehouse(
        "platform_stats", limit=999
    )

    params = execute.await_args.args[1]
    assert params["limit"] == 100
    assert params["start_date"] == "1970-01-01"
    assert params["end_date"] == "2100-01-01"
    payload = json.loads(result)
    assert payload["dataset"] == "platform_stats"
    assert payload["rows"] == [[1, 2]]
    assert payload["rowCount"] == 1
    assert payload["source"] == "ClickHouse ADS"


# limit 下界收敛为 1
@pytest.mark.anyio
async def test_query_clamps_lower_limit_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    execute = AsyncMock(return_value=[])
    monkeypatch.setattr(warehouse_module, "execute_clickhouse_query", execute)

    await ClickHouseWarehouseTools().query_warehouse("top_articles", limit=0)

    assert execute.await_args.args[1]["limit"] == 1


# ClickHouse 查询异常包装为查询失败消息
@pytest.mark.anyio
async def test_query_wraps_clickhouse_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = RuntimeError("clickhouse down")
    monkeypatch.setattr(
        warehouse_module, "execute_clickhouse_query", AsyncMock(side_effect=error)
    )

    result = await ClickHouseWarehouseTools().query_warehouse("platform_stats")

    assert result == Messages.WAREHOUSE_QUERY_FAILED.format(error=error)


# 结果列映射与数据集配置一致
def test_result_columns_follows_dataset_mapping() -> None:
    columns = ClickHouseWarehouseTools._result_columns("platform_stats")

    assert columns == WarehouseScripts.WAREHOUSE_AGENT_RESULT_COLUMNS["platform_stats"]


# 暴露的列表与查询工具名称与常量一致
def test_get_langchain_tools_exposes_list_and_query_tools() -> None:
    tool = ClickHouseWarehouseTools()

    assert [item.name for item in tool.get_langchain_tools()] == [
        Messages.WAREHOUSE_LIST_DATASETS_TOOL_NAME,
        Messages.WAREHOUSE_QUERY_TOOL_NAME,
    ]
