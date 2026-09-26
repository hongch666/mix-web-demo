"""NestjsSqlTool 远程 SQL 代理工具的单元测试"""

import json
from unittest.mock import AsyncMock

import pytest

from app.core.constants import Messages
from app.internal.agents.toolScope import clear_tool_scope, set_tool_scope
from app.internal.agents.tools.nestjsSqlTool import NestjsSqlTool


@pytest.fixture(autouse=True)
def _clear_scope() -> None:
    clear_tool_scope()
    yield
    clear_tool_scope()


def _tool() -> tuple[NestjsSqlTool, AsyncMock]:
    client = AsyncMock()
    return NestjsSqlTool(client), client


# 表结构请求透传表名并返回远程 schema 载荷
@pytest.mark.anyio
async def test_get_tables_returns_schema_payload() -> None:
    tool, client = _tool()
    client.get_tables.return_value = [{"table": "t", "columns": ["id"]}]

    result = await tool.get_tables("t")

    assert json.loads(result) == [{"table": "t", "columns": ["id"]}]
    client.get_tables.assert_awaited_once_with("t")


# 表名为空时向客户端传 None 查询全部
@pytest.mark.anyio
async def test_get_tables_passes_none_when_table_blank() -> None:
    tool, client = _tool()
    client.get_tables.return_value = [{"table": "t"}]

    await tool.get_tables("")

    client.get_tables.assert_awaited_once_with(None)


# 客户端返回空时给出无表结构消息
@pytest.mark.anyio
async def test_get_tables_returns_empty_message_when_client_has_no_data() -> None:
    tool, client = _tool()
    client.get_tables.return_value = []

    assert await tool.get_tables("t") == Messages.SQL_TOOL_NO_TABLE_SCHEMA


# 客户端异常时包装为 NestJS 表结构获取失败消息
@pytest.mark.anyio
async def test_get_tables_wraps_client_failure() -> None:
    tool, client = _tool()
    client.get_tables.side_effect = RuntimeError("remote down")

    assert await tool.get_tables("t") == Messages.SQL_TOOL_TABLE_SCHEMA_FAILED(
        "NestJS", RuntimeError("remote down")
    )


# 空语句被拒绝且不调用远程客户端
@pytest.mark.anyio
async def test_execute_query_rejects_empty_statement() -> None:
    tool, client = _tool()

    assert await tool.execute_query("") == Messages.SQL_TOOL_QUERY_EMPTY
    client.execute_query.assert_not_awaited()


# 非管理员作用域下被拒绝且不调用远程客户端
@pytest.mark.anyio
async def test_execute_query_denies_non_admin_scope() -> None:
    tool, client = _tool()
    set_tool_scope(user_id=7, is_admin=False)

    result = await tool.execute_query("SELECT id FROM t LIMIT 10", {"user_id": 7})

    assert result == Messages.NON_ADMIN_ARBITRARY_QUERY_FORBIDDEN
    client.execute_query.assert_not_awaited()


# 管理员查询返回远程结果并透传 SQL 与参数
@pytest.mark.anyio
async def test_execute_query_returns_remote_result_for_admin() -> None:
    tool, client = _tool()
    client.execute_query.return_value = {"columns": ["id"], "rows": [[1]]}
    set_tool_scope(user_id=1, is_admin=True)

    result = await tool.execute_query("SELECT id FROM t LIMIT 10", {"a": 1})

    assert json.loads(result) == {"columns": ["id"], "rows": [[1]]}
    client.execute_query.assert_awaited_once_with("SELECT id FROM t LIMIT 10", {"a": 1})


# 管理员查询异常时包装为 NestJS 查询失败消息
@pytest.mark.anyio
async def test_execute_query_wraps_client_failure() -> None:
    tool, client = _tool()
    client.execute_query.side_effect = RuntimeError("remote down")
    set_tool_scope(user_id=1, is_admin=True)

    result = await tool.execute_query("SELECT id FROM t LIMIT 10")

    assert result == Messages.SQL_TOOL_QUERY_FAILED(
        "NestJS", RuntimeError("remote down")
    )


# 暴露的表查询与查询工具名称与常量一致
def test_get_langchain_tools_exposes_table_and_query_tools() -> None:
    tool, _ = _tool()

    assert [item.name for item in tool.get_langchain_tools()] == [
        Messages.SQL_TOOL_NESTJS_TABLE_TOOL_NAME,
        Messages.SQL_TOOL_NESTJS_QUERY_TOOL_NAME,
    ]
