from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.internal.clients import nestjsClient as module


@pytest.fixture
def remote(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    call = AsyncMock(return_value={"code": 200, "data": {}})
    monkeypatch.setattr(module, "call_remote_service", call)
    return call


@pytest.fixture
def client() -> module.NestjsClient:
    return module.NestjsClient()


# 取接口平均耗时缺少 data 时返回空列表
@pytest.mark.anyio
async def test_get_api_average_speed_defaults_to_empty_list(
    remote: AsyncMock, client: module.NestjsClient
) -> None:
    remote.return_value = {"code": 200}

    assert await client.get_api_average_speed() == []
    remote.assert_awaited_once_with(
        service_name="nestjs",
        path="/api-logs/average-speed",
        method="GET",
    )


# 文章浏览分布缺少 data 时返回零值与空文章列表结构
@pytest.mark.anyio
async def test_get_article_view_distribution_returns_default_shape_when_missing(
    remote: AsyncMock, client: module.NestjsClient
) -> None:
    remote.return_value = {"code": 200}

    result = await client.get_article_view_distribution(7)

    assert result == {"total_views": 0, "articles": []}
    assert remote.await_args.kwargs["path"] == "/article-logs/view-distribution/7"


# 查询 MongoDB 组装请求体并把空 filter 补为空字典
@pytest.mark.anyio
async def test_query_mongodb_builds_body_and_defaults_filter_to_empty_dict(
    remote: AsyncMock, client: module.NestjsClient
) -> None:
    remote.return_value = {"code": 200, "data": [{"_id": "1"}]}

    assert await client.query_mongodb("apiLogs", None, 20) == [{"_id": "1"}]
    remote.assert_awaited_once_with(
        service_name="nestjs",
        path="/mongo-tools/query",
        method="POST",
        json={"collection_name": "apiLogs", "filter": {}, "limit": 20},
    )


# 同步文章日志转发游标与条数，缺少 data 时返回空列表与空游标
@pytest.mark.anyio
async def test_sync_article_logs_forwards_cursor_and_defaults_response(
    remote: AsyncMock, client: module.NestjsClient
) -> None:
    remote.return_value = {"code": 200}

    result = await client.sync_article_logs("cursor-1", 500)

    assert result == {"list": [], "nextCursor": None}
    remote.assert_awaited_once_with(
        service_name="nestjs",
        path="/article-logs/sync",
        method="GET",
        params={"cursor": "cursor-1", "limit": 500},
    )


# 上传文件从配置读取重试次数与超时并透传给远程调用
@pytest.mark.anyio
async def test_upload_file_uses_remote_call_config_for_retries_and_timeout(
    monkeypatch: pytest.MonkeyPatch, remote: AsyncMock
) -> None:
    monkeypatch.setattr(
        module,
        "load_config",
        lambda section: {"upload_timeout": 120, "max_retries": 5},
    )
    remote.return_value = {"code": 200, "data": {"url": "https://oss.local/a.png"}}

    result = await module.NestjsClient().upload_file("local/a.png", "remote/a.png")

    assert result == {"code": 200, "data": {"url": "https://oss.local/a.png"}}
    remote.assert_awaited_once_with(
        service_name="nestjs",
        path="/upload",
        method="POST",
        json={"local_file": "local/a.png", "oss_file": "remote/a.png"},
        retries=5,
        timeout=120,
    )


# 上传配置为空时回退默认重试 3 次与超时 300 秒
@pytest.mark.anyio
async def test_upload_file_falls_back_to_default_config(
    monkeypatch: pytest.MonkeyPatch, remote: AsyncMock
) -> None:
    monkeypatch.setattr(module, "load_config", lambda section: {})
    remote.return_value = {"code": 200}

    await module.NestjsClient().upload_file("a", "b")

    assert remote.await_args.kwargs["retries"] == 3
    assert remote.await_args.kwargs["timeout"] == 300


# 取表列表仅在传入表名时携带 params 过滤，否则为 None
@pytest.mark.anyio
async def test_get_tables_passes_filter_only_when_provided(
    remote: AsyncMock, client: module.NestjsClient
) -> None:
    remote.return_value = {"code": 200, "data": []}

    assert await client.get_tables("user") == []
    assert remote.await_args.kwargs["params"] == {"table": "user"}

    remote.reset_mock()
    remote.return_value = {"code": 200, "data": [{"name": "t"}]}

    assert await client.get_tables() == [{"name": "t"}]
    assert remote.await_args.kwargs["params"] is None


# 执行 SQL 提交 query 与 params，缺省时补空参数字典
@pytest.mark.anyio
async def test_execute_query_posts_query_and_defaults_params(
    remote: AsyncMock, client: module.NestjsClient
) -> None:
    remote.return_value = {"code": 200, "data": {"rows": 1}}

    assert await client.execute_query("SELECT 1", {"a": 1}) == {"rows": 1}
    assert remote.await_args.kwargs["json"] == {
        "query": "SELECT 1",
        "params": {"a": 1},
    }

    remote.reset_mock()
    remote.return_value = {"code": 200, "data": {}}

    assert await client.execute_query("SELECT 2") == {}
    assert remote.await_args.kwargs["json"] == {"query": "SELECT 2", "params": {}}


# 远程调用抛异常时原样向上抛出给调用方
@pytest.mark.anyio
async def test_downstream_failure_propagates_to_caller(
    remote: AsyncMock, client: module.NestjsClient
) -> None:
    remote.side_effect = RuntimeError("downstream boom")

    with pytest.raises(RuntimeError, match="downstream boom"):
        await client.get_called_count()


# 列出 MongoDB 集合返回 data 中的集合名列表
@pytest.mark.anyio
async def test_list_mongodb_collections_returns_data(
    remote: AsyncMock, client: module.NestjsClient
) -> None:
    remote.return_value = {"code": 200, "data": ["apiLogs", "articleLogs"]}

    result: Any = await client.list_mongodb_collections()

    assert result == ["apiLogs", "articleLogs"]
    remote.assert_awaited_once_with(
        service_name="nestjs",
        path="/mongo-tools/collections",
        method="GET",
    )


# 工厂函数返回经 lru_cache 缓存的同一 NestjsClient 实例
def test_factory_returns_lru_cached_singleton() -> None:
    module.get_nestjs_client.cache_clear()
    try:
        assert module.get_nestjs_client() is module.get_nestjs_client()
        assert isinstance(module.get_nestjs_client(), module.NestjsClient)
    finally:
        module.get_nestjs_client.cache_clear()
