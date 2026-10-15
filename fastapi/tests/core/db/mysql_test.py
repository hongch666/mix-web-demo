from collections.abc import AsyncGenerator
from typing import Any

import pytest

from app.core.db import mysql as mysql_module


class _FakeConnection:
    """替代 SQLAlchemy 连接边界，记录 run_sync 收到的回调"""

    def __init__(self) -> None:
        self.ran: list[Any] = []

    async def run_sync(self, fn: Any) -> None:
        self.ran.append(fn)


class _FakeBegin:
    def __init__(self, connection: _FakeConnection, error: Exception | None) -> None:
        self._connection = connection
        self._error = error

    async def __aenter__(self) -> _FakeConnection:
        if self._error is not None:
            raise self._error
        return self._connection

    async def __aexit__(self, *args: Any) -> bool:
        return False


class _FakeEngine:
    """替代 async_engine 的 begin() 上下文"""

    def __init__(self, error: Exception | None = None) -> None:
        self.connection = _FakeConnection()
        self._error = error

    def begin(self) -> _FakeBegin:
        return _FakeBegin(self.connection, self._error)


class _FakeSessionContext:
    """替代 AsyncSessionLocal() 的异步上下文"""

    def __init__(self, session: Any) -> None:
        self._session = session

    async def __aenter__(self) -> Any:
        return self._session

    async def __aexit__(self, *args: Any) -> bool:
        return False


# 建表把 SQLAlchemy 元数据的 create_all 交给连接执行
@pytest.mark.anyio
async def test_create_tables_async_runs_create_all(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _FakeEngine()
    monkeypatch.setattr(mysql_module, "async_engine", engine)
    logged: list[str] = []
    monkeypatch.setattr(mysql_module.Logger, "info", logged.append)

    await mysql_module.create_tables_async()

    assert engine.connection.ran == [mysql_module.Base.metadata.create_all]
    assert logged


# 建表异常时记录错误与堆栈且不向上抛，避免阻断启动
@pytest.mark.anyio
async def test_create_tables_async_swallows_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mysql_module, "async_engine", _FakeEngine(OSError("db unavailable"))
    )
    errors: list[str] = []
    monkeypatch.setattr(mysql_module.Logger, "error", errors.append)

    await mysql_module.create_tables_async()

    assert len(errors) == 2
    assert errors[1].startswith("Traceback")


# 会话依赖每次产出一个会话对象并在退出时关闭
@pytest.mark.anyio
async def test_get_db_yields_single_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = object()
    monkeypatch.setattr(
        mysql_module, "AsyncSessionLocal", lambda: _FakeSessionContext(session)
    )

    generator: AsyncGenerator[Any, None] = mysql_module.get_db()

    assert await anext(generator) is session
    with pytest.raises(StopAsyncIteration):
        await anext(generator)
