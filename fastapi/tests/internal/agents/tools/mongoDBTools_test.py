"""MongoDBTools 日志查询工具的单元测试"""

import json
from unittest.mock import AsyncMock

import pytest

from app.core.constants import Messages
from app.internal.agents.toolScope import clear_tool_scope, set_tool_scope
from app.internal.agents.tools.mongoDBTools import MongoDBTools


@pytest.fixture(autouse=True)
def _clear_scope() -> None:
    clear_tool_scope()
    yield
    clear_tool_scope()


def _tool() -> tuple[MongoDBTools, AsyncMock]:
    client = AsyncMock()
    return MongoDBTools(client), client


# 列出集合返回远程载荷且仅调用一次
@pytest.mark.anyio
async def test_list_collections_returns_payload() -> None:
    tool, client = _tool()
    client.list_mongodb_collections.return_value = [{"name": "apilogs", "count": 3}]

    result = await tool.list_mongodb_collections()

    assert json.loads(result) == [{"name": "apilogs", "count": 3}]
    client.list_mongodb_collections.assert_awaited_once_with()


# 列出集合异常时包装为集合列表获取失败消息
@pytest.mark.anyio
async def test_list_collections_wraps_client_failure() -> None:
    tool, client = _tool()
    client.list_mongodb_collections.side_effect = RuntimeError("remote down")

    assert (
        await tool.list_mongodb_collections()
        == Messages.MONGODB_COLLECTION_LIST_FAILED(RuntimeError("remote down"))
    )


# 集合名为空时返回校验错误且不调用远程
@pytest.mark.anyio
async def test_query_rejects_missing_collection_name() -> None:
    tool, client = _tool()

    assert await tool.query_mongodb("") == Messages.COLLECTION_NAME_VALIDATION_ERROR
    client.query_mongodb.assert_not_awaited()


# 非管理员作用域下查询被拒绝且不调用远程
@pytest.mark.anyio
async def test_query_denies_non_admin_scope() -> None:
    tool, client = _tool()
    set_tool_scope(user_id=7, is_admin=False)

    result = await tool.query_mongodb("apilogs", {"userId": 7}, 10)

    assert result == Messages.NON_ADMIN_ARBITRARY_QUERY_FORBIDDEN
    client.query_mongodb.assert_not_awaited()


# 管理员查询返回记录并把字符串 limit 转为整数
@pytest.mark.anyio
async def test_query_returns_records_and_coerces_limit_for_admin() -> None:
    tool, client = _tool()
    client.query_mongodb.return_value = [{"_id": "1", "userId": 7}]
    set_tool_scope(user_id=1, is_admin=True)

    result = await tool.query_mongodb("apilogs", {"userId": 7}, "3")

    assert json.loads(result) == [{"_id": "1", "userId": 7}]
    client.query_mongodb.assert_awaited_once_with("apilogs", {"userId": 7}, 3)


# 管理员查询异常时包装为日志查询失败消息
@pytest.mark.anyio
async def test_query_wraps_client_failure() -> None:
    tool, client = _tool()
    client.query_mongodb.side_effect = RuntimeError("remote down")
    set_tool_scope(user_id=1, is_admin=True)

    result = await tool.query_mongodb("apilogs", {}, 10)

    assert result == Messages.MONGODB_QUERY_FAILED(RuntimeError("remote down"))


# 暴露的列表与查询工具名称与常量一致
def test_get_langchain_tools_exposes_list_and_query_tools() -> None:
    tool, _ = _tool()

    assert [item.name for item in tool.get_langchain_tools()] == [
        Messages.MONGODB_LIST_COLLECTIONS_TOOL_NAME,
        Messages.MONGODB_QUERY_TOOL_NAME,
    ]
