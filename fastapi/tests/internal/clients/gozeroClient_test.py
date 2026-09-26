from unittest.mock import AsyncMock

import pytest

from app.internal.clients import gozeroClient as module


@pytest.fixture
def remote(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    call = AsyncMock(return_value={"code": 200, "data": {}})
    monkeypatch.setattr(module, "call_remote_service", call)
    return call


@pytest.fixture
def client() -> module.GozeroClient:
    return module.GozeroClient()


# GozeroClient 的 SERVICE_NAME 常量固定为 gozero
def test_service_name_is_gozero(client: module.GozeroClient) -> None:
    assert client.SERVICE_NAME == "gozero"


# 取表列表仅在传入表名时携带 params 过滤，否则为 None
@pytest.mark.anyio
async def test_get_tables_passes_filter_only_when_provided(
    remote: AsyncMock, client: module.GozeroClient
) -> None:
    remote.return_value = {"code": 200, "data": [{"name": "user"}]}

    assert await client.get_tables("user") == [{"name": "user"}]
    remote.assert_awaited_once_with(
        service_name="gozero",
        path="/sql-tools/tables",
        method="GET",
        params={"table": "user"},
    )

    remote.reset_mock()
    remote.return_value = {"code": 200, "data": []}

    assert await client.get_tables() == []
    assert remote.await_args.kwargs["params"] is None


# 执行 SQL 用 POST 提交 query 并在缺省时补空 params
@pytest.mark.anyio
async def test_execute_query_posts_query_and_defaults_params(
    remote: AsyncMock, client: module.GozeroClient
) -> None:
    remote.return_value = {"code": 200, "data": {"rows": 1}}

    assert await client.execute_query("SELECT 1") == {"rows": 1}
    remote.assert_awaited_once_with(
        service_name="gozero",
        path="/sql-tools/query",
        method="POST",
        json={"query": "SELECT 1", "params": {}},
    )


# 执行 SQL 显式传入 params 时原样转发到请求体
@pytest.mark.anyio
async def test_execute_query_forwards_explicit_params(
    remote: AsyncMock, client: module.GozeroClient
) -> None:
    remote.return_value = {"code": 200, "data": {"rows": 0}}

    assert await client.execute_query("SELECT :id", {"id": 7}) == {"rows": 0}
    assert remote.await_args.kwargs["json"] == {
        "query": "SELECT :id",
        "params": {"id": 7},
    }


# 远程调用抛异常时原样向上抛出给调用方
@pytest.mark.anyio
async def test_downstream_failure_propagates_to_caller(
    remote: AsyncMock, client: module.GozeroClient
) -> None:
    remote.side_effect = RuntimeError("downstream boom")

    with pytest.raises(RuntimeError, match="downstream boom"):
        await client.get_tables()


# 工厂函数返回经 lru_cache 缓存的同一 GozeroClient 实例
def test_factory_returns_lru_cached_singleton() -> None:
    module.get_gozero_client.cache_clear()
    try:
        assert module.get_gozero_client() is module.get_gozero_client()
        assert isinstance(module.get_gozero_client(), module.GozeroClient)
    finally:
        module.get_gozero_client.cache_clear()
