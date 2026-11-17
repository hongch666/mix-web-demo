"""依赖装配中 Agent 工具工厂集合的缓存行为测试"""

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest

import app.dependencies.tools as tools_module


@pytest.fixture
def clear_tool_factories_cache() -> Iterator[None]:
    """隔离工具工厂集合的进程缓存，避免用例之间共享装配结果"""
    tools_module.build_agent_tool_factories.cache_clear()
    yield
    tools_module.build_agent_tool_factories.cache_clear()


def test_provide_agent_tool_factories_reuses_instance_for_same_dependencies(
    clear_tool_factories_cache: None,
) -> None:
    """同一组依赖单例重复装配返回同一工具工厂集合，使模型服务缓存命中"""
    spring = MagicMock(name="spring-client")
    gozero = MagicMock(name="gozero-client")
    nestjs = MagicMock(name="nestjs-client")
    vector = MagicMock(name="vector-mapper")

    first = tools_module.provide_agent_tool_factories(spring, gozero, nestjs, vector)
    second = tools_module.provide_agent_tool_factories(spring, gozero, nestjs, vector)

    assert first is second


def test_provide_agent_tool_factories_separates_different_dependencies(
    clear_tool_factories_cache: None,
) -> None:
    """不同客户端单例装配出不同的工具工厂集合"""
    first = tools_module.provide_agent_tool_factories(
        MagicMock(), MagicMock(), MagicMock(), MagicMock()
    )
    second = tools_module.provide_agent_tool_factories(
        MagicMock(), MagicMock(), MagicMock(), MagicMock()
    )

    assert first is not second
