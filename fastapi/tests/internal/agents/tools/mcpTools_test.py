"""MCP 工具装配与调用的单元测试"""

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import BaseModel

from app.core.constants import Messages
from app.internal.agents.tools import mcpTools as mcp_module
from app.internal.agents.tools.mcpTools import (
    MCPServerTools,
    MCP_TOOL_NAME_PREFIX,
    get_mcp_tools,
)


class _FakeEngine:
    """替换临时 SQLAlchemy 引擎，仅记录 dispose 是否被调用"""

    def __init__(self) -> None:
        self.disposed = False

    async def dispose(self) -> None:
        self.disposed = True


class _FakeSessionFactory:
    """替换 async_sessionmaker，提供可 async with 的假会话"""

    def __init__(self, db: object) -> None:
        self._db = db

    def __call__(self) -> "_FakeSessionFactory":
        return self

    async def __aenter__(self) -> object:
        return self._db

    async def __aexit__(self, *args: object) -> None:
        return None


class _FakeMapper:
    """替换 MCP 配置 Mapper，返回预置的启用配置列表"""

    def __init__(self, configs: list[Any]) -> None:
        self.configs = configs
        self.db_seen: object = None

    async def list_enabled_async(self, db: object) -> list[Any]:
        self.db_seen = db
        return list(self.configs)


class _FakeConfig:
    """替换 McpServerConfig，保留被测代码读取的字段与方法"""

    def __init__(self, name: str, description: str = "") -> None:
        self.server_name = name
        self.description = description

    def to_connection_config(self) -> dict[str, Any]:
        return {"transport": "stdio", "command": "mcp-server", "args": []}


class _Args(BaseModel):
    """远程工具参数 schema 替身，StructuredTool 要求 args_schema 必填"""

    query: str = ""


def _remote_tool(
    name: str, description: Any = None, args_schema: Any = _Args
) -> SimpleNamespace:
    """构造最小的远程工具替身"""
    return SimpleNamespace(
        name=name,
        description=description,
        args_schema=args_schema,
        ainvoke=AsyncMock(return_value="remote result"),
    )


def _patch_infrastructure(
    monkeypatch: pytest.MonkeyPatch, mapper: _FakeMapper
) -> _FakeEngine:
    """打桩临时数据库引擎、会话与日志，使配置读取不触碰真实 DB"""
    engine = _FakeEngine()
    db = object()
    monkeypatch.setattr(mcp_module, "create_async_engine", lambda *a, **k: engine)
    monkeypatch.setattr(
        mcp_module,
        "async_sessionmaker",
        lambda *a, **k: _FakeSessionFactory(db),
    )
    monkeypatch.setattr(
        mcp_module, "Logger", SimpleNamespace(info=Mock(), warning=Mock(), error=Mock())
    )
    return engine


def _patch_mcp_client(
    monkeypatch: pytest.MonkeyPatch,
    tools_by_key: dict[str, list[Any]] | None = None,
    fail_keys: set[str] | None = None,
) -> list[str]:
    """打桩 MCP 客户端，按连接 key 返回工具或抛异常，记录每次连接的 key"""
    tools_by_key = tools_by_key or {}
    fail_keys = fail_keys or set()
    connected: list[str] = []

    class _Client:
        def __init__(self, connections: dict[str, Any]) -> None:
            # 每个实例锁定自己的 key，避免并发 gather 下互相覆盖判断
            self.key = next(iter(connections))
            connected.append(self.key)

        async def get_tools(self) -> list[Any]:
            if self.key in fail_keys:
                raise RuntimeError("mcp service down")
            return tools_by_key.get(self.key, [])

    monkeypatch.setattr(mcp_module, "MultiServerMCPClient", _Client)
    return connected


def _build_tools(mapper: _FakeMapper) -> MCPServerTools:
    return MCPServerTools(mapper)


# 服务名清洗把非法字符统一替换为下划线
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("simple", "simple"),
        ("my server-v2.0", "my_server_v2_0"),
        ("服务A", "__A"),
        ("a/b\\c:d", "a_b_c_d"),
    ],
)
def test_sanitize_server_name_replaces_illegal_characters(
    raw: str, expected: str
) -> None:
    assert MCPServerTools._sanitize_server_name(raw) == expected


# 工厂每次返回独立实例并保留注入的 Mapper
def test_get_mcp_tools_returns_new_instance_with_injected_mapper() -> None:
    mapper = _FakeMapper([])

    first = get_mcp_tools(mapper)
    second = get_mcp_tools(mapper)

    assert first is not second
    assert first._mapper is mapper
    assert second._mapper is mapper


# 连接配置以清洗后的服务名为 key 并转发实体转换结果
def test_build_connections_uses_sanitized_key() -> None:
    config = _FakeConfig("my server")

    connections = MCPServerTools._build_connections(config, "my_server")

    assert list(connections) == ["my_server"]
    assert connections["my_server"]["transport"] == "stdio"


# 无启用服务时返回空工具列表且不建立 MCP 连接
@pytest.mark.anyio
async def test_load_tools_returns_empty_when_no_enabled_servers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mapper = _FakeMapper([])
    engine = _patch_infrastructure(monkeypatch, mapper)
    connected = _patch_mcp_client(monkeypatch)

    tools = await _build_tools(mapper)._load_tools_async()

    assert tools == []
    assert connected == []
    assert engine.disposed is True


# 单个服务发现失败时隔离异常，其余服务工具正常返回
@pytest.mark.anyio
async def test_load_tools_isolates_failed_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mapper = _FakeMapper([_FakeConfig("good"), _FakeConfig("bad")])
    _patch_infrastructure(monkeypatch, mapper)
    _patch_mcp_client(
        monkeypatch,
        tools_by_key={"good": [_remote_tool("ping")]},
        fail_keys={"bad"},
    )

    tools = await _build_tools(mapper)._load_tools_async()

    assert [tool.name for tool in tools] == [f"{MCP_TOOL_NAME_PREFIX}good_ping"]


# 发现的工具按服务名加前缀，描述为空时回退到配置描述
@pytest.mark.anyio
async def test_discover_tools_prefixes_name_and_falls_back_description(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mapper = _FakeMapper([])
    _patch_infrastructure(monkeypatch, mapper)
    _patch_mcp_client(monkeypatch, tools_by_key={"my_server": [_remote_tool("search")]})
    tools = _build_tools(mapper)

    result = await tools._discover_server_tools(_FakeConfig("my server", "配置描述"))

    assert [tool.name for tool in result] == [f"{MCP_TOOL_NAME_PREFIX}my_server_search"]
    assert result[0].description == "配置描述"


# 包装保留工具名前缀与描述，并透传远程工具的 schema
def test_wrap_remote_tool_keeps_metadata_and_schema() -> None:
    tools = _build_tools(_FakeMapper([]))
    remote = _remote_tool("lookup", description="远程描述")

    wrapped = tools._wrap_remote_tool(_FakeConfig("svc"), remote)

    assert wrapped.name == f"{MCP_TOOL_NAME_PREFIX}svc_lookup"
    assert wrapped.description == "远程描述"
    assert wrapped.args_schema is _Args


# 包装工具的协程把参数原样转发给短连接调用
@pytest.mark.anyio
async def test_wrapped_tool_forwards_arguments_to_invoker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools = _build_tools(_FakeMapper([]))
    config = _FakeConfig("svc")
    remote = _remote_tool("lookup")
    wrapped = tools._wrap_remote_tool(config, remote)
    invoker = AsyncMock(return_value="result")
    monkeypatch.setattr(tools, "_invoke_remote_tool", invoker)

    assert await wrapped.coroutine(city="beijing") == "result"
    invoker.assert_awaited_once_with(config, "lookup", {"city": "beijing"})


# 调用远程工具时按短连接找到目标并执行
@pytest.mark.anyio
async def test_invoke_remote_tool_awaits_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_infrastructure(monkeypatch, _FakeMapper([]))
    remote = _remote_tool("search")
    _patch_mcp_client(monkeypatch, tools_by_key={"svc": [remote]})
    tools = _build_tools(_FakeMapper([]))

    result = await tools._invoke_remote_tool(
        _FakeConfig("svc"), "search", {"q": "python"}
    )

    assert result == "remote result"
    remote.ainvoke.assert_awaited_once_with({"q": "python"})


# 目标工具不存在时返回可读提示而非抛异常
@pytest.mark.anyio
async def test_invoke_remote_tool_returns_not_found_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_infrastructure(monkeypatch, _FakeMapper([]))
    _patch_mcp_client(monkeypatch, tools_by_key={"svc": [_remote_tool("other")]})
    tools = _build_tools(_FakeMapper([]))

    result = await tools._invoke_remote_tool(_FakeConfig("svc"), "missing", {})

    assert result == Messages.MCP_TOOL_NOT_FOUND("svc", "missing")


# 连接或执行异常时返回可读错误文案供模型参考
@pytest.mark.anyio
async def test_invoke_remote_tool_returns_error_message_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_infrastructure(monkeypatch, _FakeMapper([]))
    _patch_mcp_client(monkeypatch, fail_keys={"svc"})
    tools = _build_tools(_FakeMapper([]))

    result = await tools._invoke_remote_tool(_FakeConfig("svc"), "search", {})

    assert result.startswith("执行 svc MCP 服务工具 search 失败:")
