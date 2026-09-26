"""AgentToolFactories 工具装配工厂的单元测试"""

import dataclasses
from collections.abc import Callable
from typing import Any

import pytest

from app.internal.agents import toolFactories as tool_factories_module
from app.internal.agents.toolFactories import (
    _default_rag_tools,
    default_agent_tool_factories,
)


# 默认工厂保持 SQL 工具为 FastAPI、Spring、GoZero、NestJS 声明顺序
def test_default_agent_tool_factories_keeps_sql_tools_in_declared_order() -> None:
    factories = default_agent_tool_factories()

    assert [name for name, _ in factories.sql_tools] == [
        "FastAPI",
        "Spring",
        "GoZero",
        "NestJS",
    ]


# 各组工具绑定到对应工厂函数且标识与实现一一对应
def test_default_agent_tool_factories_binds_each_group_to_the_matching_factory() -> (
    None
):
    factories = default_agent_tool_factories()

    sql_factories: list[Callable[[], Any]] = [
        factory for _, factory in factories.sql_tools
    ]
    assert sql_factories == [
        tool_factories_module.get_fastapi_sql_tool,
        tool_factories_module.get_spring_sql_tool,
        tool_factories_module.get_gozero_sql_tool,
        tool_factories_module.get_nestjs_sql_tool,
    ]
    assert factories.rag[1] is _default_rag_tools
    assert factories.neo4j[0] == "Neo4j 知识图谱"
    assert factories.neo4j[1] is tool_factories_module.get_neo4j_tools
    assert factories.mongodb[0] == "MongoDB 日志"
    assert factories.mongodb[1] is tool_factories_module.get_mongodb_tools
    assert factories.warehouse[0] == "ClickHouse 数仓"
    assert factories.warehouse[1] is tool_factories_module.get_warehouse_tools


# 冻结的数据类实例被赋值时抛出 FrozenInstanceError
def test_agent_tool_factories_is_frozen() -> None:
    factories = default_agent_tool_factories()

    with pytest.raises(dataclasses.FrozenInstanceError):
        factories.mongodb = ("其它", lambda: None)  # type: ignore[misc]


# 默认 RAG 工具用向量 Mapper 单例构造并透传该实例
def test_default_rag_tools_resolves_vector_mapper_singleton(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mapper = object()
    captured: dict[str, Any] = {}

    def fake_get_rag_tools(vector_mapper: Any) -> str:
        captured["mapper"] = vector_mapper
        return "rag-tools"

    monkeypatch.setattr(
        tool_factories_module, "get_vector_store_mapper", lambda: mapper
    )
    monkeypatch.setattr(tool_factories_module, "get_rag_tools", fake_get_rag_tools)

    assert _default_rag_tools() == "rag-tools"
    assert captured["mapper"] is mapper
