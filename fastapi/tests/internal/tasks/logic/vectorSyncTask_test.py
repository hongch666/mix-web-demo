from collections.abc import Generator
from contextlib import nullcontext
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.constants import RedisKeys
from app.internal.tasks.logic import vectorSyncTask as task


class FakeRedisClient:
    """最小化模拟 Redis 客户端，覆盖锁与 hash/时间戳读写"""

    def __init__(self, lock_value: str | None = "lock-value") -> None:
        self.try_lock = AsyncMock(return_value=lock_value)
        self.unlock = AsyncMock(return_value=True)
        self.get = AsyncMock(return_value=None)
        self.set = AsyncMock()
        self.delete = AsyncMock()


@pytest.fixture(autouse=True)
def silence_logger(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """向量同步任务打日志密集，测试中静默日志并隔离 langsmith 上下文"""
    monkeypatch.setattr(task, "Logger", Mock())
    monkeypatch.setattr(task, "get_langsmith_context", lambda **_: nullcontext())
    yield


def _patch_sources(
    monkeypatch: pytest.MonkeyPatch,
    *,
    pages: list[dict],
    vector_mapper: Mock,
    redis_client: FakeRedisClient | None = None,
) -> Mock:
    spring_client = Mock()
    spring_client.get_published_articles = AsyncMock(side_effect=pages)
    monkeypatch.setattr(task, "get_spring_client", lambda: spring_client)
    monkeypatch.setattr(task, "get_vector_store_mapper", lambda: vector_mapper)
    monkeypatch.setattr(task, "_get_redis_client", lambda: redis_client)
    return spring_client


# 文章字段读取兼容字典与对象属性，缺失字段返回默认值
def test_get_article_field_supports_dict_and_object() -> None:
    class _Article:
        title = "orm-title"

    assert task._get_article_field({"title": "dict-title"}, "title") == "dict-title"
    assert task._get_article_field(_Article(), "title") == "orm-title"
    assert (
        task._get_article_field({"title": "dict-title"}, "content", "fallback")
        == "fallback"
    )


# 标题内容标签首尾空白被忽略且哈希为 32 位
def test_compute_article_hash_ignores_surrounding_whitespace() -> None:
    padded = task._compute_article_hash(
        {"title": " 标题 ", "content": " 内容", "tags": " go "}
    )
    plain = task._compute_article_hash(
        {"title": "标题", "content": "内容", "tags": "go"}
    )

    assert padded == plain
    assert len(padded) == 32


# 内容变化后文章哈希值随之改变
def test_compute_article_hash_changes_with_content() -> None:
    before = task._compute_article_hash({"title": "标题", "content": "旧内容"})
    after = task._compute_article_hash({"title": "标题", "content": "新内容"})

    assert before != after


# 首次无水位时只返回已发布文章并保存其哈希
@pytest.mark.anyio
async def test_changed_articles_returns_all_published_on_first_sync(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved: list[int] = []

    async def fake_save(article_id: int, hash_value: str) -> None:
        saved.append(article_id)

    monkeypatch.setattr(task, "_save_article_content_hash", fake_save)
    articles = [
        {"id": 1, "status": 1, "title": "a", "content": "x"},
        {"id": 2, "status": 0, "title": "b", "content": "y"},
    ]

    changed = await task._get_changed_articles(articles, None)

    assert [item["id"] for item in changed] == [1]
    assert saved == [1]


# 哈希未变化的文章被跳过且不重新保存
@pytest.mark.anyio
async def test_changed_articles_skips_unchanged_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    article = {"id": 1, "status": 1, "title": "a", "content": "x"}
    monkeypatch.setattr(
        task,
        "_get_article_content_hash",
        AsyncMock(return_value=task._compute_article_hash(article)),
    )
    save = AsyncMock()
    monkeypatch.setattr(task, "_save_article_content_hash", save)

    changed = await task._get_changed_articles([article], datetime(2026, 1, 1))

    assert changed == []
    save.assert_not_awaited()


# 首次出现与内容变更的文章都被纳入并保存哈希
@pytest.mark.anyio
async def test_changed_articles_includes_new_and_modified_articles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    new_article = {"id": 1, "status": 1, "title": "a", "content": "x"}
    modified_article = {"id": 2, "status": 1, "title": "b", "content": "y"}
    cached = {1: None, 2: "stale-hash"}
    monkeypatch.setattr(
        task,
        "_get_article_content_hash",
        AsyncMock(side_effect=lambda article_id: cached[article_id]),
    )
    save = AsyncMock()
    monkeypatch.setattr(task, "_save_article_content_hash", save)

    changed = await task._get_changed_articles(
        [new_article, modified_article], datetime(2026, 1, 1)
    )

    assert [item["id"] for item in changed] == [1, 2]
    assert save.await_count == 2


# 缺少 id 的文章被跳过且不保存哈希
@pytest.mark.anyio
async def test_changed_articles_skips_articles_without_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(task, "_get_article_content_hash", AsyncMock(return_value=None))
    save = AsyncMock()
    monkeypatch.setattr(task, "_save_article_content_hash", save)

    changed = await task._get_changed_articles(
        [{"status": 1, "title": "a"}], datetime(2026, 1, 1)
    )

    assert changed == []
    save.assert_not_awaited()


# 删除向量库中多出的文章并清理对应内容哈希缓存
@pytest.mark.anyio
async def test_remove_stale_vectors_deletes_diff_and_content_hashes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vector_mapper = Mock()
    vector_mapper.list_article_ids = AsyncMock(return_value={1, 2, 3})
    vector_mapper.delete_by_article_ids = AsyncMock(return_value=2)
    redis_client = FakeRedisClient()
    monkeypatch.setattr(task, "_get_redis_client", lambda: redis_client)

    deleted = await task._remove_stale_vectors(vector_mapper, [{"id": 1}])

    assert deleted == 2
    vector_mapper.delete_by_article_ids.assert_awaited_once_with([2, 3])
    redis_client.delete.assert_awaited_once_with(
        RedisKeys.article_content_hash(2), RedisKeys.article_content_hash(3)
    )


# 无多余向量时不执行删除与缓存清理
@pytest.mark.anyio
async def test_remove_stale_vectors_skips_when_nothing_stale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vector_mapper = Mock()
    vector_mapper.list_article_ids = AsyncMock(return_value={1})
    vector_mapper.delete_by_article_ids = AsyncMock()
    redis_client = FakeRedisClient()
    monkeypatch.setattr(task, "_get_redis_client", lambda: redis_client)

    deleted = await task._remove_stale_vectors(vector_mapper, [{"id": 1}])

    assert deleted == 0
    vector_mapper.delete_by_article_ids.assert_not_awaited()
    redis_client.delete.assert_not_awaited()


# Redis 不可用时仍完成多余向量的删除
@pytest.mark.anyio
async def test_remove_stale_vectors_tolerates_missing_redis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vector_mapper = Mock()
    vector_mapper.list_article_ids = AsyncMock(return_value={5})
    vector_mapper.delete_by_article_ids = AsyncMock(return_value=1)
    monkeypatch.setattr(task, "_get_redis_client", lambda: None)

    assert await task._remove_stale_vectors(vector_mapper, []) == 1


# 拉取已发布文章失败时提前返回且不写入向量
@pytest.mark.anyio
async def test_export_returns_when_article_fetch_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vector_mapper = Mock()
    vector_mapper.upsert_articles = AsyncMock()
    spring_client = Mock()
    spring_client.get_published_articles = AsyncMock(
        side_effect=RuntimeError("spring unavailable")
    )
    monkeypatch.setattr(task, "get_spring_client", lambda: spring_client)
    monkeypatch.setattr(task, "get_vector_store_mapper", lambda: vector_mapper)
    monkeypatch.setattr(task, "_get_redis_client", lambda: FakeRedisClient())

    await task._export_article_vectors_to_postgres()

    vector_mapper.upsert_articles.assert_not_awaited()


# 快照分页不完整时跳过差集清理且不写入向量
@pytest.mark.anyio
async def test_export_skips_stale_cleanup_when_snapshot_incomplete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vector_mapper = Mock()
    vector_mapper.list_article_ids = AsyncMock(return_value={1, 2})
    vector_mapper.delete_by_article_ids = AsyncMock(return_value=1)
    vector_mapper.upsert_articles = AsyncMock()
    _patch_sources(
        monkeypatch,
        pages=[
            {"records": [{"id": 1, "status": 1}], "total": 50},
            {"records": [], "total": 50},
        ],
        vector_mapper=vector_mapper,
        redis_client=FakeRedisClient(),
    )
    monkeypatch.setattr(
        task, "_get_last_sync_time", AsyncMock(return_value=datetime(2026, 1, 1))
    )
    monkeypatch.setattr(task, "_get_changed_articles", AsyncMock(return_value=[]))

    await task._export_article_vectors_to_postgres()

    # 分页不完整时差集口径失效，必须跳过快照清理
    vector_mapper.delete_by_article_ids.assert_not_awaited()
    vector_mapper.upsert_articles.assert_not_awaited()


# 无变更文章时不写入向量也不更新同步时间
@pytest.mark.anyio
async def test_export_returns_when_no_changed_articles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vector_mapper = Mock()
    vector_mapper.list_article_ids = AsyncMock(return_value={1})
    vector_mapper.delete_by_article_ids = AsyncMock(return_value=0)
    vector_mapper.upsert_articles = AsyncMock()
    _patch_sources(
        monkeypatch,
        pages=[{"records": [{"id": 1, "status": 1}], "total": 1}],
        vector_mapper=vector_mapper,
        redis_client=FakeRedisClient(),
    )
    monkeypatch.setattr(
        task, "_get_last_sync_time", AsyncMock(return_value=datetime(2026, 1, 1))
    )
    monkeypatch.setattr(task, "_get_changed_articles", AsyncMock(return_value=[]))
    save_time = AsyncMock()
    monkeypatch.setattr(task, "_save_sync_time", save_time)

    await task._export_article_vectors_to_postgres()

    vector_mapper.upsert_articles.assert_not_awaited()
    save_time.assert_not_awaited()


# 变更文章按批写入向量并携带完整元数据，完成后保存同步时间
@pytest.mark.anyio
async def test_export_upserts_batch_and_saves_sync_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    article = {
        "id": 9,
        "status": 1,
        "title": "标题",
        "content": "内容",
        "tags": "go",
        "user_id": 3,
        "views": 5,
    }
    vector_mapper = Mock()
    vector_mapper.list_article_ids = AsyncMock(return_value={9})
    vector_mapper.delete_by_article_ids = AsyncMock(return_value=1)
    vector_mapper.upsert_articles = AsyncMock(return_value=1)
    _patch_sources(
        monkeypatch,
        pages=[{"records": [article], "total": 1}],
        vector_mapper=vector_mapper,
        redis_client=FakeRedisClient(),
    )
    monkeypatch.setattr(
        task, "_get_last_sync_time", AsyncMock(return_value=datetime(2026, 1, 1))
    )
    monkeypatch.setattr(
        task, "_get_changed_articles", AsyncMock(return_value=[article])
    )
    save_time = AsyncMock()
    monkeypatch.setattr(task, "_save_sync_time", save_time)

    await task._export_article_vectors_to_postgres()

    upsert_kwargs = vector_mapper.upsert_articles.await_args.kwargs
    assert upsert_kwargs["article_ids"] == [9]
    assert upsert_kwargs["titles"] == ["标题"]
    assert upsert_kwargs["contents"] == ["内容"]
    assert upsert_kwargs["metadata_list"] == [
        {
            "user_id": 3,
            "tags": "go",
            "status": 1,
            "views": 5,
            "create_at": "",
            "update_at": "",
        }
    ]
    save_time.assert_awaited_once()


# 分批写入全部失败重试后不更新同步时间
@pytest.mark.anyio
async def test_export_does_not_save_sync_time_when_all_batches_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    article = {"id": 9, "status": 1, "title": "t", "content": "c", "tags": ""}
    vector_mapper = Mock()
    vector_mapper.list_article_ids = AsyncMock(return_value={9})
    vector_mapper.delete_by_article_ids = AsyncMock(return_value=0)
    vector_mapper.upsert_articles = AsyncMock(side_effect=RuntimeError("upsert failed"))
    _patch_sources(
        monkeypatch,
        pages=[{"records": [article], "total": 1}],
        vector_mapper=vector_mapper,
        redis_client=FakeRedisClient(),
    )
    monkeypatch.setattr(
        task, "_get_last_sync_time", AsyncMock(return_value=datetime(2026, 1, 1))
    )
    monkeypatch.setattr(
        task, "_get_changed_articles", AsyncMock(return_value=[article])
    )
    save_time = AsyncMock()
    monkeypatch.setattr(task, "_save_sync_time", save_time)
    sleep = AsyncMock()
    monkeypatch.setattr(task, "asyncio", Mock(sleep=sleep))

    await task._export_article_vectors_to_postgres()

    assert vector_mapper.upsert_articles.await_count == 3
    assert sleep.await_count == 2
    save_time.assert_not_awaited()


# 关闭增量同步时仅推送已发布文章且不更新增量时间
@pytest.mark.anyio
async def test_export_full_mode_uses_published_articles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    published = {"id": 1, "status": 1, "title": "a", "content": "x", "tags": ""}
    draft = {"id": 2, "status": 0, "title": "b", "content": "y", "tags": ""}
    vector_mapper = Mock()
    vector_mapper.list_article_ids = AsyncMock(return_value={1})
    vector_mapper.delete_by_article_ids = AsyncMock(return_value=0)
    vector_mapper.upsert_articles = AsyncMock(return_value=1)
    _patch_sources(
        monkeypatch,
        pages=[{"records": [published, draft], "total": 2}],
        vector_mapper=vector_mapper,
        redis_client=FakeRedisClient(),
    )
    save_time = AsyncMock()
    monkeypatch.setattr(task, "_save_sync_time", save_time)

    await task._export_article_vectors_to_postgres(enable_incremental_sync=False)

    assert vector_mapper.upsert_articles.await_args.kwargs["article_ids"] == [1]
    save_time.assert_not_awaited()


# 未获取到分布式锁时跳过向量导出且不释放锁
@pytest.mark.anyio
async def test_export_async_skips_when_lock_is_not_acquired(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedisClient(None)
    export = AsyncMock()
    monkeypatch.setattr(task, "get_redis_client", lambda: redis_client)
    monkeypatch.setattr(task, "_export_article_vectors_to_postgres", export)

    await task.export_article_vectors_to_postgres_async()

    export.assert_not_awaited()
    redis_client.unlock.assert_not_awaited()
    redis_client.try_lock.assert_awaited_once_with(
        RedisKeys.LOCK_TASK_VECTOR_SYNC, RedisKeys.LOCK_TASK_VECTOR_SYNC_EXPIRE
    )


# 获取锁后透传增量开关给导出函数并释放锁
@pytest.mark.anyio
async def test_export_async_unlocks_and_forwards_incremental_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedisClient()
    export = AsyncMock()
    monkeypatch.setattr(task, "get_redis_client", lambda: redis_client)
    monkeypatch.setattr(task, "_export_article_vectors_to_postgres", export)

    await task.export_article_vectors_to_postgres_async(enable_incremental_sync=False)

    export.assert_awaited_once_with(None, None, False)
    redis_client.unlock.assert_awaited_once_with(
        RedisKeys.LOCK_TASK_VECTOR_SYNC, "lock-value"
    )


# 初始化哈希缓存时只补缺少的文章并保存同步时间
@pytest.mark.anyio
async def test_hash_init_skips_existing_hashes_and_saves_timestamp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    articles = [
        {"id": 1, "status": 1, "title": "a", "content": "x"},
        {"id": 2, "status": 1, "title": "b", "content": "y"},
        {"id": 3, "status": 0, "title": "c", "content": "z"},
    ]
    spring_client = Mock()
    spring_client.get_published_articles = AsyncMock(
        return_value={"records": articles, "total": 3}
    )
    monkeypatch.setattr(task, "get_spring_client", lambda: spring_client)
    monkeypatch.setattr(
        task, "_get_article_content_hash", AsyncMock(side_effect=["existing", None])
    )
    save = AsyncMock()
    monkeypatch.setattr(task, "_save_article_content_hash", save)
    save_time = AsyncMock()
    monkeypatch.setattr(task, "_save_sync_time", save_time)

    await task._initialize_article_content_hash_cache()

    save.assert_awaited_once()
    assert save.await_args.args[0] == 2
    save_time.assert_awaited_once()


# 无已发布文章时不保存同步时间
@pytest.mark.anyio
async def test_hash_init_returns_when_no_articles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spring_client = Mock()
    spring_client.get_published_articles = AsyncMock(
        return_value={"records": [], "total": 0}
    )
    monkeypatch.setattr(task, "get_spring_client", lambda: spring_client)
    save_time = AsyncMock()
    monkeypatch.setattr(task, "_save_sync_time", save_time)

    await task._initialize_article_content_hash_cache()

    save_time.assert_not_awaited()


# 同步时间戳按 ISO 字符串解析为 datetime
@pytest.mark.anyio
async def test_get_last_sync_time_parses_iso_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedisClient()
    redis_client.get = AsyncMock(return_value="2026-09-01T10:00:00")
    monkeypatch.setattr(task, "_get_redis_client", lambda: redis_client)

    assert await task._get_last_sync_time() == datetime(2026, 9, 1, 10, 0, 0)


# Redis 读取异常时同步时间戳返回 None
@pytest.mark.anyio
async def test_get_last_sync_time_returns_none_on_redis_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedisClient()
    redis_client.get = AsyncMock(side_effect=RuntimeError("redis down"))
    monkeypatch.setattr(task, "_get_redis_client", lambda: redis_client)

    assert await task._get_last_sync_time() is None


# 保存时间戳写入 ISO 字符串且吞掉 Redis 异常
@pytest.mark.anyio
async def test_save_sync_time_swallows_redis_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedisClient()
    redis_client.set = AsyncMock(side_effect=RuntimeError("redis down"))
    monkeypatch.setattr(task, "_get_redis_client", lambda: redis_client)

    await task._save_sync_time(datetime(2026, 9, 1))

    redis_client.set.assert_awaited_once_with(
        RedisKeys.VECTOR_SYNC_TIME, "2026-09-01T00:00:00"
    )


# Redis 不可用时文章哈希读写均静默跳过
@pytest.mark.anyio
async def test_article_hash_access_is_noop_without_redis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(task, "_get_redis_client", lambda: None)

    assert await task._get_article_content_hash(1) is None
    await task._save_article_content_hash(1, "hash-value")
