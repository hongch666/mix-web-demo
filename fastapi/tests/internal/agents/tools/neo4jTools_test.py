"""Neo4jQueryTools 知识图谱工具的单元测试"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.constants import Messages, Scripts
from app.internal.agents.tools import neo4jTools as neo4j_module
from app.internal.agents.tools.neo4jTools import Neo4jQueryTools


class _FakeNeo4jClient:
    def __init__(self, connect_result: bool = True) -> None:
        self.connect = AsyncMock(return_value=connect_result)
        self.run_query = AsyncMock(return_value=[])


def _raising_get_client() -> Neo4jQueryTools:
    raise RuntimeError("no db")


def _tools(
    monkeypatch: pytest.MonkeyPatch, client: _FakeNeo4jClient
) -> Neo4jQueryTools:
    monkeypatch.setattr(neo4j_module, "get_neo4j_client", lambda: client)
    return Neo4jQueryTools()


# 客户端缺失时预定义查询返回服务不可用消息
@pytest.mark.anyio
async def test_predefined_query_returns_unavailable_when_client_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(neo4j_module, "get_neo4j_client", _raising_get_client)
    tool = Neo4jQueryTools()

    assert tool.client is None
    assert (
        await tool.execute_predefined_query("article_detail")
        == Messages.NEO4J_SERVICE_UNAVAILABLE_MESSAGE
    )


# 客户端连接失败时预定义查询返回服务不可用消息
@pytest.mark.anyio
async def test_predefined_query_returns_unavailable_when_connect_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _tools(monkeypatch, _FakeNeo4jClient(connect_result=False))

    assert (
        await tool.execute_predefined_query("article_detail")
        == Messages.NEO4J_SERVICE_UNAVAILABLE_MESSAGE
    )


# 预定义查询格式化 OGM 记录并跳过空值字段
@pytest.mark.anyio
async def test_predefined_query_formats_ogm_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _tools(monkeypatch, _FakeNeo4jClient())
    records = [{"title": "文章A", "views": 10, "tags": ["x", "y"], "empty": None}]
    monkeypatch.setitem(
        tool._ogm_handlers, "article_detail", AsyncMock(return_value=records)
    )

    result = await tool.execute_predefined_query("article_detail")

    assert Messages.NEO4J_QUERY_RESULT_HEADER("article_detail", 1) in result
    assert "title: 文章A" in result
    assert "tags: x, y" in result
    assert "empty" not in result


# OGM 处理抛异常时返回无结果消息
@pytest.mark.anyio
async def test_predefined_query_returns_no_result_when_handler_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _tools(monkeypatch, _FakeNeo4jClient())
    monkeypatch.setitem(
        tool._ogm_handlers,
        "article_detail",
        AsyncMock(side_effect=RuntimeError("ogm boom")),
    )

    assert (
        await tool.execute_predefined_query("article_detail")
        == Messages.NEO4J_NO_RESULT_MESSAGE
    )


# 不支持的查询名返回不支持提示
@pytest.mark.anyio
async def test_predefined_query_rejects_unknown_query_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _tools(monkeypatch, _FakeNeo4jClient())

    result = await tool.execute_predefined_query("not_supported")

    assert result.startswith("不支持的查询类型")


# 预定义查询将 Cypher 路由到客户端并携带默认 limit
@pytest.mark.anyio
async def test_predefined_query_routes_raw_cypher_to_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _tools(monkeypatch, _FakeNeo4jClient())
    monkeypatch.setitem(Scripts.INTENT_TO_CYPHER, "unit_query", "MATCH (n) RETURN n")
    tool.client.run_query.return_value = [{"id": 1}]

    result = await tool.execute_predefined_query("unit_query")

    assert Messages.NEO4J_QUERY_RESULT_HEADER("unit_query", 1) in result
    assert tool.client.run_query.await_args.args[0] == "MATCH (n) RETURN n"
    assert tool.client.run_query.await_args.args[1]["limit"] == 10


# 自定义 Cypher 返回序列化后的记录
@pytest.mark.anyio
async def test_custom_cypher_returns_serialized_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _tools(monkeypatch, _FakeNeo4jClient())
    tool.client.run_query.return_value = [{"title": "A"}]

    result = await tool.execute_custom_cypher("MATCH (n) RETURN n")

    assert json.loads(result) == [{"title": "A"}]
    tool.client.run_query.assert_awaited_once_with("MATCH (n) RETURN n")


# 自定义 Cypher 含写操作时被只读限制拦截且不执行
@pytest.mark.anyio
async def test_custom_cypher_rejects_write_statement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _tools(monkeypatch, _FakeNeo4jClient())

    result = await tool.execute_custom_cypher("MATCH (n) DELETE n")

    assert result == Messages.NEO4J_READ_ONLY_LIMIT_MESSAGE
    tool.client.run_query.assert_not_awaited()


# 自定义 Cypher 无记录时返回空结果消息
@pytest.mark.anyio
async def test_custom_cypher_returns_empty_message_when_no_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool = _tools(monkeypatch, _FakeNeo4jClient())
    tool.client.run_query.return_value = []

    assert (
        await tool.execute_custom_cypher("MATCH (n) RETURN n")
        == Messages.NEO4J_QUERY_EMPTY_MESSAGE
    )


# 客户端缺失时自定义 Cypher 返回服务不可用消息
@pytest.mark.anyio
async def test_custom_cypher_returns_unavailable_when_client_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(neo4j_module, "get_neo4j_client", _raising_get_client)
    tool = Neo4jQueryTools()

    assert (
        await tool.execute_custom_cypher("MATCH (n) RETURN n")
        == Messages.NEO4J_SERVICE_UNAVAILABLE_MESSAGE
    )


# 只读 Cypher 判定拒绝空串、SELECT 与写操作
@pytest.mark.parametrize(
    ("cypher", "expected"),
    [
        ("MATCH (n) RETURN n", True),
        ("  OPTIONAL MATCH (n) RETURN n ", True),
        ("WITH 1 AS x RETURN x", True),
        ("CALL DB.INDEXES() YIELD name RETURN name", True),
        ("RETURN 1", True),
        ("", False),
        ("SELECT * FROM t", False),
        ("MATCH (n) SET n.x = 1", False),
        ("MATCH (n) DELETE n", False),
        ("MATCH (n); MATCH (m) RETURN n", False),
    ],
)
def test_is_read_only_cypher_guards(cypher: str, expected: bool) -> None:
    assert Neo4jQueryTools._is_read_only_cypher(cypher) is expected


# limit 参数按边界收敛为默认值与范围内整数
@pytest.mark.parametrize(
    ("params", "expected_limit"),
    [
        ({}, 10),
        ({"limit": "abc"}, 10),
        ({"limit": 0}, 1),
        ({"limit": 999}, 50),
        ({"limit": 20}, 20),
    ],
)
def test_normalize_limit_clamps_and_defaults(params: dict, expected_limit: int) -> None:
    normalized = Neo4jQueryTools._normalize_limit(params)

    assert normalized["limit"] == expected_limit


# 归一化 limit 时不修改传入的参数字典
def test_normalize_limit_does_not_mutate_input() -> None:
    params = {"limit": 999}

    Neo4jQueryTools._normalize_limit(params)

    assert params == {"limit": 999}


# 关联名称读取预加载关系、缺失时返回 None
def test_related_name_reads_preloaded_relation() -> None:
    related = SimpleNamespace(name="张三", _relations={})
    node = SimpleNamespace(_relations={"author": [related]})

    assert Neo4jQueryTools._related_name(node, "author") == "张三"
    assert (
        Neo4jQueryTools._related_name(SimpleNamespace(_relations={}), "author") is None
    )


# 可用查询名合并 OGM 与 Cypher 两组名称
def test_available_query_names_merges_ogm_and_cypher(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(neo4j_module, "get_neo4j_client", lambda: _FakeNeo4jClient())
    tool = Neo4jQueryTools()

    names = tool.available_query_names

    assert "article_detail" in names
    assert "top_viewed_articles" in names
    for key in Scripts.INTENT_TO_CYPHER:
        assert key in names


# get_neo4j_tools 工厂清缓存前后返回同一实例
def test_get_neo4j_tools_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(neo4j_module, "get_neo4j_client", lambda: _FakeNeo4jClient())
    neo4j_module.get_neo4j_tools.cache_clear()
    try:
        first = neo4j_module.get_neo4j_tools()
        second = neo4j_module.get_neo4j_tools()
    finally:
        neo4j_module.get_neo4j_tools.cache_clear()

    assert first is second
