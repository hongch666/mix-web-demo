from collections.abc import Generator
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.constants import RedisKeys, Scripts
from app.internal.tasks.logic import neo4jSyncTask as task


class FakeRedisClient:
    """最小化模拟 Redis 客户端，只覆盖同步时间戳读写"""

    def __init__(self, lock_value: str | None = "lock-value") -> None:
        self.try_lock = AsyncMock(return_value=lock_value)
        self.unlock = AsyncMock(return_value=True)
        self.get = AsyncMock(return_value=None)
        self.set = AsyncMock()


class SummaryWithoutCounters:
    """模拟没有 counters 属性的 Neo4j 结果摘要"""


@pytest.fixture(autouse=True)
def silence_logger(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Neo4j 同步任务日志密集，测试中静默日志"""
    monkeypatch.setattr(task, "Logger", Mock())
    yield


def _build_service(
    monkeypatch: pytest.MonkeyPatch, neo4j_client: Mock
) -> task.KnowledgeGraphSyncService:
    monkeypatch.setattr(task, "get_neo4j_client", lambda: neo4j_client)
    monkeypatch.setattr(task, "get_spring_client", lambda: Mock())
    return task.KnowledgeGraphSyncService()


# 时间格式化对 datetime 取 ISO 串、字符串直通、None 用当前时间
def test_format_datetime_handles_datetime_text_and_empty() -> None:
    fixed = datetime(2026, 9, 1, 12, 0, 0)

    assert task.KnowledgeGraphSyncService._format_datetime(fixed) == fixed.isoformat()
    assert task.KnowledgeGraphSyncService._format_datetime("2026-09-01") == "2026-09-01"
    assert datetime.fromisoformat(task.KnowledgeGraphSyncService._format_datetime(None))


# 关系键按 用户:目标:类型 三段以冒号拼接
def test_build_relation_key_joins_parts_with_colon() -> None:
    assert task.KnowledgeGraphSyncService._build_relation_key(1, 2, "go") == "1:2:go"


# 摘要或 counters 缺失时删除计数为 0，否则累加节点与关系删除数
def test_extract_deleted_count_handles_missing_counters() -> None:
    assert task.KnowledgeGraphSyncService._extract_deleted_count(None) == 0
    assert (
        task.KnowledgeGraphSyncService._extract_deleted_count(SummaryWithoutCounters())
        == 0
    )

    counters = Mock(nodes_deleted=2, relationships_deleted=3)
    assert (
        task.KnowledgeGraphSyncService._extract_deleted_count(Mock(counters=counters))
        == 5
    )


# 用户字段映射并补角色邮箱默认值，跳过缺少 id 的行
def test_normalize_users_maps_fields_and_skips_missing_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _build_service(monkeypatch, Mock())
    rows = [
        {"id": "1", "name": "alice", "role": None, "created_at": None},
        {"name": "no-id"},
    ]

    users = service._normalize_users(rows)

    assert len(users) == 1
    assert users[0]["id"] == 1
    assert users[0]["name"] == "alice"
    assert users[0]["role"] == "user"
    assert users[0]["email"] == ""
    assert users[0]["signature"] == ""


# 文章归一化转换数值字段并计算内容哈希与标签关系，跳过缺 id 行
def test_normalize_articles_computes_hash_and_tag_relations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _build_service(monkeypatch, Mock())
    rows = [
        {
            "id": "7",
            "title": "标题",
            "content": "内容",
            "tags": "go, python",
            "status": 1,
            "views": "3",
            "user_id": "2",
            "sub_category_id": None,
        },
        {"id": None},
    ]

    articles = service._normalize_articles(rows)

    assert len(articles) == 1
    assert articles[0]["views"] == 3
    assert articles[0]["userId"] == 2
    assert articles[0]["subCategoryId"] is None
    assert articles[0]["contentHash"] == service._compute_content_hash(
        "标题", "内容", "go, python"
    )
    assert service._build_article_tag_relations(articles) == [
        {"articleId": 7, "tagName": "go"},
        {"articleId": 7, "tagName": "python"},
    ]


# 点赞与关注记录缺少用户或目标时被跳过
def test_normalize_likes_and_focus_skip_incomplete_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _build_service(monkeypatch, Mock())

    likes = service._normalize_likes(
        [
            {"user_id": "1", "article_id": "2", "created_time": None},
            {"user_id": None, "article_id": "3"},
            {"user_id": "4", "article_id": None},
        ]
    )
    focus = service._normalize_focus(
        [{"user_id": "1", "focus_id": "2"}, {"user_id": None, "focus_id": "3"}]
    )

    assert [item["articleId"] for item in likes] == [2]
    assert [item["followerId"] for item in focus] == [1]
    assert [item["followedId"] for item in focus] == [2]


# 建图 schema 按约束脚本数量逐条执行写查询
@pytest.mark.anyio
async def test_ensure_schema_runs_all_constraint_scripts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock(run_write_query=AsyncMock())
    service = _build_service(monkeypatch, client)

    await service._ensure_schema()

    assert client.run_write_query.await_count == len(Scripts.NEO4J_CREATE_CONSTRAINTS)


# 空行集直接返回 0 且不发起写查询
@pytest.mark.anyio
async def test_batch_write_returns_zero_for_empty_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock(run_write_query=AsyncMock())
    service = _build_service(monkeypatch, client)

    assert await service._batch_write([], "CYPHER", "用户") == 0
    client.run_write_query.assert_not_awaited()


# 1201 行按 500 分批写入为 500/500/201 并返回总数 1201
@pytest.mark.anyio
async def test_batch_write_splits_rows_into_batches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock(run_write_query=AsyncMock())
    service = _build_service(monkeypatch, client)
    rows = [{"id": index} for index in range(1201)]

    written = await service._batch_write(rows, "CYPHER", "用户", batch_size=500)

    assert written == 1201
    assert client.run_write_query.await_count == 3
    batch_sizes = [
        len(call.args[1]["rows"]) for call in client.run_write_query.await_args_list
    ]
    assert batch_sizes == [500, 500, 201]


# 保留键为空时跳过清理且不发起写查询
@pytest.mark.anyio
async def test_cleanup_write_skips_empty_keep_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock(run_write_query=AsyncMock())
    service = _build_service(monkeypatch, client)

    assert await service._cleanup_write("CYPHER", {"ids": []}, "文章") == 0
    assert await service._cleanup_write("CYPHER", {"keys": []}, "关系") == 0
    client.run_write_query.assert_not_awaited()


# 2500 个关系键按 1000 分批执行 3 次写查询
@pytest.mark.anyio
async def test_cleanup_write_batches_relation_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock(run_write_query=AsyncMock(return_value=None))
    service = _build_service(monkeypatch, client)
    keys = [f"key-{index}" for index in range(2500)]

    deleted = await service._cleanup_write("CYPHER", {"keys": keys}, "关系")

    assert deleted == 0
    assert client.run_write_query.await_count == 3
    batch_sizes = [
        len(call.args[1]["keys"]) for call in client.run_write_query.await_args_list
    ]
    assert batch_sizes == [1000, 1000, 500]


# 节点清理一次性传入完整 id 集合而非分批
@pytest.mark.anyio
async def test_cleanup_write_sends_node_ids_in_single_batch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock(run_write_query=AsyncMock(return_value=None))
    service = _build_service(monkeypatch, client)
    ids = list(range(2500))

    await service._cleanup_write("CYPHER", {"ids": ids}, "节点")

    # 节点清理必须一次传入完整集合，分批会误删集合之外的节点
    client.run_write_query.assert_awaited_once_with("CYPHER", {"ids": ids})


# 清理返回的摘要计数累加为节点与关系删除总数
@pytest.mark.anyio
async def test_cleanup_write_sums_deleted_counters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    counters = Mock(nodes_deleted=2, relationships_deleted=3)
    client = Mock(run_write_query=AsyncMock(return_value=Mock(counters=counters)))
    service = _build_service(monkeypatch, client)

    assert await service._cleanup_write("CYPHER", {"ids": [1]}, "节点") == 5


# 图数据总数兼容 int 与数字字符串，非法值或空结果视为无数据
@pytest.mark.anyio
async def test_has_graph_data_reads_total_as_int(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock()
    service = _build_service(monkeypatch, client)

    client.run_query = AsyncMock(return_value=[{"total": 3}])
    assert await service._has_graph_data() is True

    client.run_query = AsyncMock(return_value=[{"total": "4"}])
    assert await service._has_graph_data() is True

    client.run_query = AsyncMock(return_value=[{"total": "unknown"}])
    assert await service._has_graph_data() is False

    client.run_query = AsyncMock(return_value=[])
    assert await service._has_graph_data() is False


# 图数据为空时增量同步回退为全量同步
@pytest.mark.anyio
async def test_sync_incremental_falls_back_to_full_sync_when_graph_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock(
        run_query=AsyncMock(return_value=[{"total": 0}]), run_write_query=AsyncMock()
    )
    service = _build_service(monkeypatch, client)
    sync_all = AsyncMock(return_value={"users": 1})
    monkeypatch.setattr(service, "sync_all", sync_all)

    result = await service.sync_incremental(datetime(2026, 9, 1))

    assert result == {"users": 1}
    sync_all.assert_awaited_once_with()


# 缺少上次同步时间时增量同步回退为全量同步
@pytest.mark.anyio
async def test_sync_incremental_falls_back_to_full_sync_without_watermark(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock(
        run_query=AsyncMock(return_value=[{"total": 2}]), run_write_query=AsyncMock()
    )
    service = _build_service(monkeypatch, client)
    sync_all = AsyncMock(return_value={})
    monkeypatch.setattr(service, "sync_all", sync_all)

    await service.sync_incremental(None)

    sync_all.assert_awaited_once_with()


# 有水位时按窗口增量抓取且不执行删除清理
@pytest.mark.anyio
async def test_sync_incremental_uses_watermark_window_and_skips_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock(
        run_query=AsyncMock(return_value=[{"total": 1}]), run_write_query=AsyncMock()
    )
    service = _build_service(monkeypatch, client)
    fetch = AsyncMock(return_value={})
    monkeypatch.setattr(service, "_fetch_snapshot", fetch)
    last_sync_time = datetime(2026, 9, 1, 8, 0, 0)

    result = await service.sync_incremental(last_sync_time)

    fetch.assert_awaited_once_with(last_sync_time)
    assert {"users", "articles", "tagged_as", "follows"} <= set(result)
    assert all(value == 0 for value in result.values())


# 全量同步汇总快照各类型节点与关系计数且不执行删除清理
@pytest.mark.anyio
async def test_sync_all_merges_snapshot_without_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock(run_write_query=AsyncMock())
    service = _build_service(monkeypatch, client)
    monkeypatch.setattr(
        service,
        "_fetch_snapshot",
        AsyncMock(
            return_value={
                "users": [{"id": "1", "name": "alice"}],
                "articles": [
                    {
                        "id": "7",
                        "title": "标题",
                        "content": "内容",
                        "tags": "go",
                        "user_id": "1",
                        "sub_category_id": None,
                    }
                ],
            }
        ),
    )
    cleanup = AsyncMock()
    monkeypatch.setattr(service, "_cleanup_deleted_graph_data", cleanup)

    result = await service.sync_all()

    assert result["users"] == 1
    assert result["articles"] == 1
    assert result["tags"] == 1
    assert result["tagged_as"] == 1
    assert result["published_by"] == 1
    cleanup.assert_not_awaited()


# 分类等基础维度始终全量抓取，其余按同步水位增量抓取
@pytest.mark.anyio
async def test_fetch_snapshot_always_fetches_base_dimensions_in_full(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Mock()
    service = _build_service(monkeypatch, client)
    spring_client = Mock()
    for method in (
        "get_neo4j_sync_users",
        "get_neo4j_sync_categories",
        "get_neo4j_sync_sub_categories",
        "get_neo4j_sync_articles",
        "get_neo4j_sync_likes",
        "get_neo4j_sync_collects",
        "get_neo4j_sync_comments",
        "get_neo4j_sync_focus",
    ):
        setattr(spring_client, method, AsyncMock(return_value=[]))
    service.spring_client = spring_client
    last_sync_time = datetime(2026, 9, 1, 8, 0, 0)

    snapshot = await service._fetch_snapshot(last_sync_time)

    assert set(snapshot) == {
        "users",
        "categories",
        "sub_categories",
        "articles",
        "likes",
        "collects",
        "comments",
        "focus",
    }
    assert spring_client.get_neo4j_sync_users.await_args.args[0] == (
        last_sync_time.isoformat()
    )
    # 分类与子分类是基础维度，始终全量抓取，避免增量窗口内无更新导致基础节点缺失
    assert spring_client.get_neo4j_sync_categories.await_args.args[0] is None
    assert spring_client.get_neo4j_sync_sub_categories.await_args.args[0] is None
    assert (
        spring_client.get_neo4j_sync_categories.await_args.kwargs["timeout"]
        == service.SYNC_FETCH_TIMEOUT
    )


# 同步产生变更时保存最新同步时间戳
@pytest.mark.anyio
async def test_sync_mysql_to_neo4j_saves_watermark_only_when_changed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sync_service = Mock(
        sync_incremental=AsyncMock(return_value={"users": 0, "articles": 2})
    )
    monkeypatch.setattr(task, "get_knowledge_graph_sync_service", lambda: sync_service)
    monkeypatch.setattr(task, "_get_last_sync_time", AsyncMock(return_value=None))
    save_time = AsyncMock()
    monkeypatch.setattr(task, "_save_sync_time", save_time)

    result = await task._sync_mysql_to_neo4j()

    assert result == {"users": 0, "articles": 2}
    save_time.assert_awaited_once()


# 同步结果无变更时不更新同步时间戳
@pytest.mark.anyio
async def test_sync_mysql_to_neo4j_skips_watermark_when_nothing_changed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sync_service = Mock(sync_incremental=AsyncMock(return_value={"users": 0}))
    monkeypatch.setattr(task, "get_knowledge_graph_sync_service", lambda: sync_service)
    monkeypatch.setattr(task, "_get_last_sync_time", AsyncMock(return_value=None))
    save_time = AsyncMock()
    monkeypatch.setattr(task, "_save_sync_time", save_time)

    await task._sync_mysql_to_neo4j()

    save_time.assert_not_awaited()


# 强制全量标记时调用全量同步并保存时间戳
@pytest.mark.anyio
async def test_sync_mysql_to_neo4j_uses_full_sync_when_forced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sync_service = Mock(sync_all=AsyncMock(return_value={"users": 1}))
    monkeypatch.setattr(task, "get_knowledge_graph_sync_service", lambda: sync_service)
    save_time = AsyncMock()
    monkeypatch.setattr(task, "_save_sync_time", save_time)

    await task._sync_mysql_to_neo4j(force_full=True)

    sync_service.sync_all.assert_awaited_once_with()
    save_time.assert_awaited_once()


# 同步抛错时吞掉异常返回空结果且不保存时间戳
@pytest.mark.anyio
async def test_sync_mysql_to_neo4j_swallows_sync_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sync_service = Mock(
        sync_incremental=AsyncMock(side_effect=RuntimeError("neo4j unavailable"))
    )
    monkeypatch.setattr(task, "get_knowledge_graph_sync_service", lambda: sync_service)
    monkeypatch.setattr(task, "_get_last_sync_time", AsyncMock(return_value=None))
    save_time = AsyncMock()
    monkeypatch.setattr(task, "_save_sync_time", save_time)

    assert await task._sync_mysql_to_neo4j() == {}
    save_time.assert_not_awaited()


# 未获取到分布式锁时跳过同步且不释放锁
@pytest.mark.anyio
async def test_sync_async_skips_when_lock_is_not_acquired(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedisClient(None)
    sync = AsyncMock()
    monkeypatch.setattr(task, "get_redis_client", lambda: redis_client)
    monkeypatch.setattr(task, "_sync_mysql_to_neo4j", sync)

    await task.sync_mysql_to_neo4j_async()

    sync.assert_not_awaited()
    redis_client.unlock.assert_not_awaited()
    redis_client.try_lock.assert_awaited_once_with(
        RedisKeys.LOCK_TASK_NEO4J_SYNC, RedisKeys.LOCK_TASK_NEO4J_SYNC_EXPIRE
    )


# 获取锁后透传全量标记给同步函数并释放锁
@pytest.mark.anyio
async def test_sync_async_forwards_full_flag_and_releases_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedisClient()
    sync = AsyncMock()
    monkeypatch.setattr(task, "get_redis_client", lambda: redis_client)
    monkeypatch.setattr(task, "_sync_mysql_to_neo4j", sync)

    await task.sync_mysql_to_neo4j_async(force_full=True)

    sync.assert_awaited_once_with(force_full=True)
    redis_client.unlock.assert_awaited_once_with(
        RedisKeys.LOCK_TASK_NEO4J_SYNC, "lock-value"
    )


# 同步时间戳按 ISO 字符串解析为 datetime
@pytest.mark.anyio
async def test_get_last_sync_time_parses_iso_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedisClient()
    redis_client.get = AsyncMock(return_value="2026-09-01T08:00:00")
    monkeypatch.setattr(task, "get_redis_client", lambda: redis_client)

    assert await task._get_last_sync_time() == datetime(2026, 9, 1, 8, 0, 0)


# Redis 读取异常时同步时间戳返回 None
@pytest.mark.anyio
async def test_get_last_sync_time_returns_none_on_redis_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedisClient()
    redis_client.get = AsyncMock(side_effect=RuntimeError("redis down"))
    monkeypatch.setattr(task, "get_redis_client", lambda: redis_client)

    assert await task._get_last_sync_time() is None


# 保存时间戳写入 ISO 字符串且吞掉 Redis 异常
@pytest.mark.anyio
async def test_save_sync_time_swallows_redis_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedisClient()
    redis_client.set = AsyncMock(side_effect=RuntimeError("redis down"))
    monkeypatch.setattr(task, "get_redis_client", lambda: redis_client)

    await task._save_sync_time(datetime(2026, 9, 1, 8, 0, 0))

    redis_client.set.assert_awaited_once_with(
        RedisKeys.NEO4J_SYNC_TIME, "2026-09-01T08:00:00"
    )
