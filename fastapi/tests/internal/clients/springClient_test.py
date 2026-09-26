from unittest.mock import AsyncMock
from typing import Any

import pytest

from app.internal.clients import springClient as module


@pytest.fixture
def remote(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    call = AsyncMock(return_value={"code": 200, "data": {}})
    monkeypatch.setattr(module, "call_remote_service", call)
    return call


@pytest.fixture
def client() -> module.SpringClient:
    return module.SpringClient()


# 同步数仓数据按服务名与分页参数发起 GET 并解包 data 字段
@pytest.mark.anyio
async def test_sync_warehouse_data_forwards_paging_and_unwraps_data(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.return_value = {"code": 200, "data": {"list": [{"id": 1}]}}

    result = await client.sync_warehouse_data("articles", "2026-01-01", page=2, size=50)

    assert result == {"list": [{"id": 1}]}
    remote.assert_awaited_once_with(
        service_name="spring",
        path="/warehouse/sync/articles",
        method="GET",
        params={"updatedAfter": "2026-01-01", "page": 2, "size": 50},
    )


# 响应缺少 data 字段时同步数仓数据返回空字典
@pytest.mark.anyio
async def test_sync_warehouse_data_returns_empty_dict_when_data_missing(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.return_value = {"code": 200}

    assert await client.sync_warehouse_data("articles", "2026-01-01") == {}


# 批量方法传入空 ID 列表时直接返回空列表或空字典且不发远程调用
@pytest.mark.anyio
@pytest.mark.parametrize(
    ("method_name", "expected"),
    [
        ("get_articles_by_ids", []),
        ("get_users_by_ids", []),
        ("get_categories_by_ids", []),
        ("get_sub_categories_by_ids", []),
        ("get_article_views_by_ids", {}),
        ("get_like_counts_by_article_ids", {}),
        ("get_collect_counts_by_article_ids", {}),
        ("get_follow_counts_by_user_ids", {}),
    ],
)
async def test_batch_methods_skip_remote_call_for_empty_ids(
    remote: AsyncMock,
    client: module.SpringClient,
    method_name: str,
    expected: Any,
) -> None:
    assert await getattr(client, method_name)([]) == expected
    remote.assert_not_awaited()


# 按 ID 批量取文章用 POST 提交 ids，缺少 data 时返回空列表
@pytest.mark.anyio
async def test_get_articles_by_ids_posts_ids_and_defaults_to_empty_list(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.return_value = {"code": 200}

    assert await client.get_articles_by_ids([1, 2]) == []

    remote.assert_awaited_once_with(
        service_name="spring",
        path="/articles/batch",
        method="POST",
        json={"ids": [1, 2]},
    )


# 按文章 ID 取浏览量返回 data 字典映射
@pytest.mark.anyio
async def test_get_article_views_by_ids_returns_data_mapping(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.return_value = {"code": 200, "data": {"1": 10}}

    assert await client.get_article_views_by_ids([1]) == {"1": 10}


# 按文章 ID 取评论评分时转发 timeout 参数并解包 data
@pytest.mark.anyio
async def test_get_comment_scores_by_article_ids_forwards_timeout(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.return_value = {"code": 200, "data": {1: {"author": 5}}}

    result = await client.get_comment_scores_by_article_ids([1], timeout=15)

    assert result == {1: {"author": 5}}
    assert remote.await_args.kwargs["path"] == "/comments/scores/batch"
    assert remote.await_args.kwargs["timeout"] == 15


# 按子分类取分类引用时缺少 data 返回 None 且路径含子分类 ID
@pytest.mark.anyio
async def test_get_category_reference_returns_none_when_data_missing(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.return_value = {"code": 200}

    assert await client.get_category_reference_by_sub_category_id(9) is None
    remote.assert_awaited_once_with(
        service_name="spring",
        path="/category/reference/sub/9",
        method="GET",
    )


# 已发布文章把 Spring 分页 total 转整型并把 list 重命名为 records
@pytest.mark.anyio
async def test_get_published_articles_normalizes_spring_page_vo(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.return_value = {"code": 200, "data": {"total": "7", "list": [{"id": 1}]}}

    result = await client.get_published_articles(page=2, size=20, timeout=8)

    assert result == {"total": 7, "records": [{"id": 1}]}
    remote.assert_awaited_once_with(
        service_name="spring",
        path="/articles/list",
        method="GET",
        params={"page": 2, "size": 20},
        timeout=8,
    )


# 分页响应缺少 total 且使用 records 字段时补零并保留记录
@pytest.mark.anyio
async def test_get_published_articles_falls_back_to_records_field(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.return_value = {"code": 200, "data": {"records": [{"id": 2}]}}

    assert await client.get_published_articles() == {
        "total": 0,
        "records": [{"id": 2}],
    }


# 总量类统计接口在缺少 data 时默认返回整数 0
@pytest.mark.anyio
@pytest.mark.parametrize(
    "method_name",
    ["get_total_views", "get_total_articles", "get_active_authors"],
)
async def test_count_statistics_default_to_zero_when_data_missing(
    remote: AsyncMock, client: module.SpringClient, method_name: str
) -> None:
    remote.return_value = {"code": 200}

    assert await getattr(client, method_name)() == 0


# 均值类统计接口在缺少 data 时默认返回浮点 0.0
@pytest.mark.anyio
@pytest.mark.parametrize(
    "method_name",
    ["get_average_views", "get_average_likes", "get_average_collects"],
)
async def test_average_statistics_default_to_zero_float_when_data_missing(
    remote: AsyncMock, client: module.SpringClient, method_name: str
) -> None:
    remote.return_value = {"code": 200}

    assert await getattr(client, method_name)() == 0.0


# 月度点赞趋势缺少 data 时返回 total 0 与空列表结构
@pytest.mark.anyio
async def test_get_monthly_like_trend_returns_default_structure_when_missing(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.return_value = {"code": 200}

    assert await client.get_monthly_like_trend(7) == {"total": 0, "daily_trends": []}
    assert remote.await_args.kwargs["path"] == "/likes/statistics/monthly-trend/7"


# 取用户文章数用单页查询读取 total 并转为整数
@pytest.mark.anyio
async def test_get_user_article_count_reads_total_from_single_page_query(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.return_value = {"code": 200, "data": {"total": "5"}}

    assert await client.get_user_article_count(7) == 5
    assert remote.await_args.kwargs["path"] == "/articles/user/7"
    assert remote.await_args.kwargs["params"] == {
        "page": 1,
        "size": 1,
        "published": 1,
    }


# 累加用户文章各条 views，忽略空值并把字符串转数字
@pytest.mark.anyio
async def test_get_user_total_views_sums_record_views(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.return_value = {
        "code": 200,
        "data": {"list": [{"views": "3"}, {"views": None}, {"views": 4}]},
    }

    assert await client.get_user_total_views(7) == 7


# 用户粉丝数兼容 data 为字典 count 或直接数值两种形态
@pytest.mark.anyio
@pytest.mark.parametrize(
    ("payload", "expected"),
    [({"count": "9"}, 9), (12, 12)],
)
async def test_get_user_total_followers_reads_dict_count_or_scalar(
    remote: AsyncMock,
    client: module.SpringClient,
    payload: Any,
    expected: int,
) -> None:
    remote.return_value = {"code": 200, "data": payload}

    assert await client.get_user_total_followers(7) == expected


# 删除文章 AI 评论以 POST 调用并返回 None
@pytest.mark.anyio
async def test_delete_ai_comments_posts_and_returns_none(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.return_value = {"code": 200}

    assert await client.delete_ai_comments_by_article_id(3) is None
    remote.assert_awaited_once_with(
        service_name="spring",
        path="/comments/statistics/delete-ai/3",
        method="POST",
    )


# 图谱同步文章转发 updated_after 水位与 timeout 并解包 data
@pytest.mark.anyio
async def test_get_neo4j_sync_articles_forwards_watermark_and_timeout(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.return_value = {"code": 200, "data": [{"id": 1}]}

    result = await client.get_neo4j_sync_articles("2026-01-01", timeout=20)

    assert result == [{"id": 1}]
    remote.assert_awaited_once_with(
        service_name="spring",
        path="/articles/neo4j-sync",
        method="GET",
        params={"updated_after": "2026-01-01"},
        timeout=20,
    )


# 图谱同步用户未传水位时 params 与 timeout 均为 None
@pytest.mark.anyio
async def test_get_neo4j_sync_users_omits_params_without_watermark(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.return_value = {"code": 200, "data": []}

    assert await client.get_neo4j_sync_users() == []
    remote.assert_awaited_once_with(
        service_name="spring",
        path="/users/neo4j-sync",
        method="GET",
        params=None,
        timeout=None,
    )


# 取表列表仅在传入表名时携带 params 过滤，否则为 None
@pytest.mark.anyio
async def test_get_tables_passes_table_filter_only_when_provided(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.return_value = {"code": 200, "data": [{"name": "user"}]}

    assert await client.get_tables("user") == [{"name": "user"}]
    assert remote.await_args.kwargs["params"] == {"table": "user"}

    remote.reset_mock()
    remote.return_value = {"code": 200, "data": []}

    assert await client.get_tables() == []
    assert remote.await_args.kwargs["params"] is None


# 执行 SQL 用 POST 提交 query 并在缺省时补空 params
@pytest.mark.anyio
async def test_execute_query_posts_query_and_defaults_params(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.return_value = {"code": 200, "data": {"rows": 2}}

    assert await client.execute_query("SELECT 1") == {"rows": 2}
    remote.assert_awaited_once_with(
        service_name="spring",
        path="/sql-tools/query",
        method="POST",
        json={"query": "SELECT 1", "params": {}},
    )


# 创建评论用 POST 提交评论体并解包 data
@pytest.mark.anyio
async def test_create_comment_posts_body_and_unwraps_data(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.return_value = {"code": 200, "data": {"id": 5}}

    assert await client.create_comment({"articleId": 1, "content": "hi"}) == {"id": 5}
    remote.assert_awaited_once_with(
        service_name="spring",
        path="/comments/internal/create",
        method="POST",
        json={"articleId": 1, "content": "hi"},
    )


# 远程调用抛异常时原样向上抛出给调用方
@pytest.mark.anyio
async def test_downstream_failure_propagates_to_caller(
    remote: AsyncMock, client: module.SpringClient
) -> None:
    remote.side_effect = RuntimeError("downstream boom")

    with pytest.raises(RuntimeError, match="downstream boom"):
        await client.get_total_views()


# 工厂函数返回经 lru_cache 缓存的同一 SpringClient 实例
def test_factory_returns_lru_cached_singleton() -> None:
    module.get_spring_client.cache_clear()
    try:
        assert module.get_spring_client() is module.get_spring_client()
        assert isinstance(module.get_spring_client(), module.SpringClient)
    finally:
        module.get_spring_client.cache_clear()
