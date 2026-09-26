"""LangSmith 客户端开关、采样与 Run 上下文的单元测试"""

from collections.abc import Generator
from types import SimpleNamespace
from typing import Any

import pytest

from app.internal.agents.langsmith import client as client_module
from app.internal.agents.langsmith.client import (
    get_langsmith_client,
    get_langsmith_config,
    get_langsmith_context,
    get_langsmith_context_async,
    init_langsmith,
    shutdown_langsmith,
)
from app.internal.agents.langsmith.config import LangSmithConfig


@pytest.fixture(autouse=True)
def _reset_langsmith_state() -> Generator[None, None, None]:
    yield
    client_module._client = None
    client_module._config = None
    client_module._init_error = None


def _config(enabled: bool = True, sampling_rate: float = 1.0) -> LangSmithConfig:
    return LangSmithConfig(
        enabled=enabled,
        api_key="unit-test-key",
        project="mix-project",
        endpoint="http://langsmith.local",
        workspace_id=None,
        hide_inputs=False,
        hide_outputs=False,
        sampling_rate=sampling_rate,
    )


def _enable_tracing(
    monkeypatch: pytest.MonkeyPatch, sampling_rate: float = 1.0
) -> None:
    monkeypatch.setattr(client_module, "_config", _config(sampling_rate=sampling_rate))
    monkeypatch.setattr(client_module, "_client", object())


class _FakeRun:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.parent_run: Any = None
        self.ended = False

    def end(self) -> None:
        self.ended = True


# 配置关闭时初始化不创建客户端且不记录错误
def test_init_langsmith_logs_disabled_state(monkeypatch: pytest.MonkeyPatch) -> None:
    # 当前 Messages 常量缺少关闭追踪提示键，注入替身以隔离被测分支
    monkeypatch.setattr(
        client_module,
        "Messages",
        SimpleNamespace(LANGSMITH_TRACING_DISABLED="LangSmith 追踪已禁用"),
    )

    init_langsmith(_config(enabled=False))

    assert client_module._client is None
    assert client_module._init_error is None
    assert get_langsmith_config() is client_module._config


# 单例缺失时初始化加载配置并构造客户端
def test_init_langsmith_loads_config_when_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 显式复位模块全局单例，确保结果与执行顺序无关
    monkeypatch.setattr(client_module, "_client", None)
    monkeypatch.setattr(client_module, "_config", None)
    monkeypatch.setattr(client_module, "_init_error", None)
    config = _config()
    monkeypatch.setattr(client_module, "load_langsmith_config", lambda: config)
    monkeypatch.setattr(client_module, "LangSmithClient", lambda **kwargs: object())

    init_langsmith()

    assert get_langsmith_config() is config
    assert client_module._client is not None


# LangSmith 依赖缺失时记录安装缺失错误且不创建客户端
def test_init_langsmith_records_missing_package(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 当前 Messages 常量缺少依赖缺失提示键，注入替身以隔离被测分支
    missing_package = "LangSmith 依赖未安装"
    monkeypatch.setattr(
        client_module,
        "Messages",
        SimpleNamespace(LANGSMITH_PACKAGE_NOT_INSTALLED=missing_package),
    )
    monkeypatch.setattr(client_module, "LangSmithClient", None)

    init_langsmith(_config())

    assert client_module._client is None
    assert client_module._init_error == missing_package


# 初始化按配置的 api_key 与 endpoint 构造客户端
def test_init_langsmith_builds_client_with_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class _FakeClient:
        def __init__(self, api_key: str, api_url: str) -> None:
            captured["api_key"] = api_key
            captured["api_url"] = api_url

    monkeypatch.setattr(client_module, "LangSmithClient", _FakeClient)

    init_langsmith(_config())

    assert captured == {"api_key": "unit-test-key", "api_url": "http://langsmith.local"}
    assert get_langsmith_client() is client_module._client


# 客户端构造抛异常时隔离失败并记录错误
def test_init_langsmith_isolates_construction_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _BrokenClient:
        def __init__(self, **kwargs: Any) -> None:
            raise RuntimeError("client init failed")

    monkeypatch.setattr(client_module, "LangSmithClient", _BrokenClient)

    init_langsmith(_config())

    assert client_module._client is None
    assert client_module._init_error is not None


# 配置关闭时获取客户端返回 None
def test_get_client_returns_none_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client_module, "_config", _config(enabled=False))
    monkeypatch.setattr(client_module, "_client", object())

    assert get_langsmith_client() is None


# 采样率按随机数决定是否返回客户端
def test_get_client_applies_sampling_rate(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = object()
    monkeypatch.setattr(client_module, "_config", _config(sampling_rate=0.5))
    monkeypatch.setattr(client_module, "_client", sentinel)

    monkeypatch.setattr(client_module, "random", SimpleNamespace(random=lambda: 0.1))
    assert get_langsmith_client() is sentinel

    monkeypatch.setattr(client_module, "random", SimpleNamespace(random=lambda: 0.9))
    assert get_langsmith_client() is None


# shutdown_langsmith 清空已创建的客户端引用
def test_shutdown_clears_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client_module, "_client", object())

    shutdown_langsmith()

    assert client_module._client is None


# 客户端禁用时同步上下文产出 None
def test_sync_context_yields_none_when_client_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client_module, "_config", _config(enabled=False))
    monkeypatch.setattr(client_module, "_client", object())

    with get_langsmith_context("chat.send") as run:
        assert run is None


# 同步上下文按参数创建 Run 并在退出时结束
def test_sync_context_creates_and_ends_run(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_tracing(monkeypatch)
    monkeypatch.setattr(client_module, "RunTree", _FakeRun)

    with get_langsmith_context("chat.send", tags=["t"], metadata={"a": 1}) as run:
        assert isinstance(run, _FakeRun)
        assert run.kwargs["name"] == "chat.send"
        assert run.kwargs["tags"] == ["t"]
        assert run.kwargs["run_type"] == "chain"

    assert run.ended is True


# 同步上下文将传入的父 Run 绑定到子 Run
def test_sync_context_binds_parent_run(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_tracing(monkeypatch)
    monkeypatch.setattr(client_module, "RunTree", _FakeRun)
    parent = object()

    with get_langsmith_context("chat.child", parent_run=parent) as run:
        assert isinstance(run, _FakeRun)
        assert run.parent_run is parent


# Run 创建失败时同步上下文产出 None
def test_sync_context_yields_none_when_run_creation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_tracing(monkeypatch)

    class _BrokenRun:
        def __init__(self, **kwargs: Any) -> None:
            raise RuntimeError("run creation failed")

    monkeypatch.setattr(client_module, "RunTree", _BrokenRun)

    with get_langsmith_context("chat.send") as run:
        assert run is None


# Run 结束抛异常时同步上下文吞掉异常不向上传播
def test_sync_context_swallows_end_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_tracing(monkeypatch)

    class _EndFailingRun(_FakeRun):
        def end(self) -> None:
            raise RuntimeError("end failed")

    monkeypatch.setattr(client_module, "RunTree", _EndFailingRun)

    with get_langsmith_context("chat.send") as run:
        assert run is not None


# 客户端禁用时异步上下文产出 None
@pytest.mark.anyio
async def test_async_context_yields_none_when_client_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(client_module, "_config", _config(enabled=False))
    monkeypatch.setattr(client_module, "_client", object())

    async with get_langsmith_context_async("chat.stream") as run:
        assert run is None


# 异步上下文按名称创建 Run 并在退出时结束
@pytest.mark.anyio
async def test_async_context_creates_and_ends_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_tracing(monkeypatch)
    monkeypatch.setattr(client_module, "RunTree", _FakeRun)

    async with get_langsmith_context_async("chat.stream") as run:
        assert isinstance(run, _FakeRun)
        assert run.kwargs["name"] == "chat.stream"

    assert run.ended is True


# Run 创建失败时异步上下文产出 None
@pytest.mark.anyio
async def test_async_context_yields_none_when_run_creation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_tracing(monkeypatch)

    class _BrokenRun:
        def __init__(self, **kwargs: Any) -> None:
            raise RuntimeError("run creation failed")

    monkeypatch.setattr(client_module, "RunTree", _BrokenRun)

    async with get_langsmith_context_async("chat.stream") as run:
        assert run is None
