from collections.abc import AsyncGenerator
from typing import Any

import pytest

from app.core.db import clickhouse as clickhouse_module


class _FakeResult:
    """替代 SQLAlchemy 结果集，只提供 fetchall"""

    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def fetchall(self) -> list[Any]:
        return self._rows


class _FakeConnection:
    """替代 ClickHouse 连接边界，记录驱动 SQL 与参数"""

    def __init__(
        self, rows: list[Any] | None = None, error: Exception | None = None
    ) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.ran: list[Any] = []
        self._rows: list[Any] = rows or []
        self._error = error

    async def exec_driver_sql(
        self, sql: str, parameters: dict[str, Any]
    ) -> _FakeResult:
        self.calls.append((sql, parameters))
        if self._error is not None:
            raise self._error
        return _FakeResult(self._rows)

    async def run_sync(self, fn: Any) -> None:
        self.ran.append(fn)


class _FakeConnect:
    def __init__(
        self, connection: _FakeConnection, error: Exception | None = None
    ) -> None:
        self._connection = connection
        self._error = error

    async def __aenter__(self) -> _FakeConnection:
        if self._error is not None:
            raise self._error
        return self._connection

    async def __aexit__(self, *args: Any) -> bool:
        return False


class _FakeEngine:
    """替代 clickhouse_async_engine 的 connect() 上下文"""

    def __init__(
        self, connection: _FakeConnection, error: Exception | None = None
    ) -> None:
        self.connection = connection
        self._error = error
        self.disposed = 0

    def connect(self) -> _FakeConnect:
        return _FakeConnect(self.connection, self._error)

    async def dispose(self) -> None:
        self.disposed += 1


class _FakeSessionContext:
    """替代 ClickHouseAsyncSessionLocal() 的异步上下文"""

    def __init__(self, session: Any) -> None:
        self._session = session

    async def __aenter__(self) -> Any:
        return self._session

    async def __aexit__(self, *args: Any) -> bool:
        return False


# 查询走参数化驱动 SQL，并把结果行统一转成元组
@pytest.mark.anyio
async def test_execute_clickhouse_query_returns_row_tuples(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = _FakeConnection(rows=[(1, "a"), (2, "b")])
    monkeypatch.setattr(
        clickhouse_module, "clickhouse_async_engine", _FakeEngine(connection)
    )

    rows: list[Any] = await clickhouse_module.execute_clickhouse_query(
        "SELECT * FROM t WHERE name = %(name)s", {"name": "x"}
    )

    assert rows == [(1, "a"), (2, "b")]
    assert connection.calls == [
        ("SELECT * FROM t WHERE name = %(name)s", {"name": "x"})
    ]


# 无返回结果的语句只执行不取数据
@pytest.mark.anyio
async def test_execute_clickhouse_sql_discards_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = _FakeConnection()
    monkeypatch.setattr(
        clickhouse_module, "clickhouse_async_engine", _FakeEngine(connection)
    )

    result: None = await clickhouse_module.execute_clickhouse_sql(
        "ALTER TABLE t DELETE WHERE 1", {}
    )

    assert result is None
    assert connection.calls == [("ALTER TABLE t DELETE WHERE 1", {})]


# 驱动异常向上传播，由调用方决定降级策略
@pytest.mark.anyio
async def test_execute_clickhouse_query_propagates_driver_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = _FakeConnection(error=OSError("clickhouse unavailable"))
    monkeypatch.setattr(
        clickhouse_module, "clickhouse_async_engine", _FakeEngine(connection)
    )

    with pytest.raises(OSError):
        await clickhouse_module.execute_clickhouse_query("SELECT 1", {})


# 会话上下文管理器产出会话并负责关闭
@pytest.mark.anyio
async def test_clickhouse_session_yields_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = object()
    monkeypatch.setattr(
        clickhouse_module,
        "ClickHouseAsyncSessionLocal",
        lambda: _FakeSessionContext(session),
    )

    async with clickhouse_module.clickhouse_session() as current:
        assert current is session


# 依赖形式的会话入口复用同一套会话创建方式
@pytest.mark.anyio
async def test_get_clickhouse_db_yields_single_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = object()
    monkeypatch.setattr(
        clickhouse_module,
        "ClickHouseAsyncSessionLocal",
        lambda: _FakeSessionContext(session),
    )

    generator: AsyncGenerator[Any, None] = clickhouse_module.get_clickhouse_db()

    assert await anext(generator) is session
    with pytest.raises(StopAsyncIteration):
        await anext(generator)


# 并发查询用的会话工厂与会话上下文保持同一个入口
def test_get_clickhouse_session_factory_returns_session_context() -> None:
    assert (
        clickhouse_module.get_clickhouse_session_factory()
        is clickhouse_module.clickhouse_session
    )


# 关闭应用时释放连接池
@pytest.mark.anyio
async def test_dispose_clickhouse_async_engine_disposes_pool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _FakeEngine(_FakeConnection())
    monkeypatch.setattr(clickhouse_module, "clickhouse_async_engine", engine)

    await clickhouse_module.dispose_clickhouse_async_engine()

    assert engine.disposed == 1


# 数仓建表把 ORM 元数据的 create_all 交给连接执行
@pytest.mark.anyio
async def test_create_warehouse_tables_async_runs_create_all(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _FakeEngine(_FakeConnection())
    monkeypatch.setattr(clickhouse_module, "clickhouse_async_engine", engine)
    logged: list[str] = []
    monkeypatch.setattr(clickhouse_module.Logger, "info", logged.append)

    await clickhouse_module.create_warehouse_tables_async()

    assert engine.connection.ran == [
        clickhouse_module.ClickHouseBase.metadata.create_all
    ]
    assert logged


# 数仓建表失败只记录错误，不阻断服务启动
@pytest.mark.anyio
async def test_create_warehouse_tables_async_swallows_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        clickhouse_module,
        "clickhouse_async_engine",
        _FakeEngine(_FakeConnection(), OSError("warehouse unavailable")),
    )
    errors: list[str] = []
    monkeypatch.setattr(clickhouse_module.Logger, "error", errors.append)

    await clickhouse_module.create_warehouse_tables_async()

    assert len(errors) == 1
