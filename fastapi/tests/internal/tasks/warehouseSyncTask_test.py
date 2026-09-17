from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.internal.tasks.logic import warehouseSyncTask as task


class FakeRedisClient:
    def __init__(self, lock_value: str | None = "lock-value") -> None:
        self.lock_value = lock_value
        self.try_lock = AsyncMock(return_value=lock_value)
        self.unlock = AsyncMock(return_value=True)


@pytest.mark.anyio
async def test_sync_warehouse_returns_when_spring_client_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_redis = AsyncMock()
    monkeypatch.setattr(task, "get_redis_client", get_redis)

    await task.sync_warehouse_async(None)

    get_redis.assert_not_called()


@pytest.mark.anyio
async def test_sync_warehouse_skips_when_lock_is_not_acquired(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedisClient(None)
    sync = AsyncMock()
    monkeypatch.setattr(task, "get_redis_client", lambda: redis_client)
    monkeypatch.setattr(task, "_sync_warehouse", sync)

    await task.sync_warehouse_async(AsyncMock())

    sync.assert_not_awaited()
    redis_client.unlock.assert_not_awaited()


@pytest.mark.anyio
async def test_sync_warehouse_releases_lock_after_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedisClient()
    sync = AsyncMock(side_effect=RuntimeError("sync failed"))
    spring_client = AsyncMock()
    monkeypatch.setattr(task, "get_redis_client", lambda: redis_client)
    monkeypatch.setattr(task, "_sync_warehouse", sync)

    with pytest.raises(RuntimeError, match="sync failed"):
        await task.sync_warehouse_async(spring_client)

    redis_client.unlock.assert_awaited_once_with(
        task.RedisKeys.LOCK_TASK_WAREHOUSE, "lock-value"
    )


@pytest.mark.anyio
async def test_remote_source_advances_watermark_only_after_all_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initial = datetime(2026, 1, 1, 0, 0, 0)
    upper = datetime(2026, 1, 2, 0, 0, 0)
    spring_client = AsyncMock()
    spring_client.sync_warehouse_data.side_effect = [
        {
            "list": [{"id": 1, "title": "first"}],
            "upperWatermark": "2026-01-02 00:00:00",
            "hasMore": True,
        },
        {
            "list": [{"id": 2, "title": "second"}],
            "upperWatermark": "2026-01-02 00:00:00",
            "hasMore": False,
        },
    ]
    insert_rows = AsyncMock()
    write_watermark = AsyncMock()
    monkeypatch.setattr(task, "_read_watermark", AsyncMock(return_value=initial))
    monkeypatch.setattr(task, "_insert_rows", insert_rows)
    monkeypatch.setattr(task, "_write_watermark", write_watermark)
    monkeypatch.setitem(task.REMOTE_MODELS, "ods_articles", object)

    await task._sync_remote_source(
        spring_client,
        "ods_articles",
        "articles",
        ("id", "title"),
    )

    assert spring_client.sync_warehouse_data.await_count == 2
    assert insert_rows.await_count == 2
    write_watermark.assert_awaited_once_with("ods_articles", upper)


@pytest.mark.anyio
async def test_remote_source_does_not_advance_watermark_when_page_insert_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spring_client = AsyncMock()
    spring_client.sync_warehouse_data.return_value = {
        "list": [{"id": 1, "title": "first"}],
        "upperWatermark": "2026-01-02 00:00:00",
        "hasMore": False,
    }
    monkeypatch.setattr(
        task,
        "_read_watermark",
        AsyncMock(return_value=datetime(2026, 1, 1, 0, 0, 0)),
    )
    monkeypatch.setattr(
        task, "_insert_rows", AsyncMock(side_effect=RuntimeError("insert failed"))
    )
    write_watermark = AsyncMock()
    monkeypatch.setattr(task, "_write_watermark", write_watermark)
    monkeypatch.setitem(task.REMOTE_MODELS, "ods_articles", object)

    with pytest.raises(RuntimeError, match="insert failed"):
        await task._sync_remote_source(
            spring_client,
            "ods_articles",
            "articles",
            ("id", "title"),
        )

    write_watermark.assert_not_awaited()
