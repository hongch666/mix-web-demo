from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.internal.tasks.logic import warehouseSyncTask as task


class FakeRedisClient:
    def __init__(self, lock_value: str | None = "lock-value") -> None:
        self.lock_value = lock_value
        self.try_lock = AsyncMock(return_value=lock_value)
        self.unlock = AsyncMock(return_value=True)


# Spring 客户端缺失时直接返回且不获取 Redis
@pytest.mark.anyio
async def test_sync_warehouse_returns_when_spring_client_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_redis = AsyncMock()
    monkeypatch.setattr(task, "get_redis_client", get_redis)

    await task.sync_warehouse_async(None)

    get_redis.assert_not_called()


# 未获取到分布式锁时跳过数仓同步且不释放锁
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


# 同步抛错时向上抛出并仍释放分布式锁
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


# 多页数据全部写入成功后才推进该源的数仓水位
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


# MySQL 快照表即使无脏分区也返回有变更标记
@pytest.mark.anyio
async def test_remote_source_reports_change_flag_for_snapshot_tables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # MySQL 源表不产生脏分区，但需要返回"有变更"以驱动快照表刷新
    spring_client = AsyncMock()
    spring_client.sync_warehouse_data.return_value = {
        "list": [{"id": 1, "name": "alice"}],
        "upperWatermark": "2026-01-02 00:00:00",
        "hasMore": False,
    }
    monkeypatch.setattr(
        task,
        "_read_watermark",
        AsyncMock(return_value=datetime(2026, 1, 1, 0, 0, 0)),
    )
    monkeypatch.setattr(task, "_insert_rows", AsyncMock())
    monkeypatch.setattr(task, "_write_watermark", AsyncMock())
    monkeypatch.setitem(task.REMOTE_MODELS, "ods_user", object)

    changed, partitions = await task._sync_remote_source(
        spring_client, "ods_user", "user", ("id", "name")
    )

    assert changed is True
    assert partitions == set()


# 源表无增量数据时返回无变更且无脏分区
@pytest.mark.anyio
async def test_remote_source_reports_no_change_when_no_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spring_client = AsyncMock()
    spring_client.sync_warehouse_data.return_value = {"list": [], "hasMore": False}
    monkeypatch.setattr(
        task, "_read_watermark", AsyncMock(return_value=datetime(2026, 1, 1))
    )
    monkeypatch.setattr(task, "_insert_rows", AsyncMock())
    monkeypatch.setitem(task.REMOTE_MODELS, "ods_user", object)

    changed, partitions = await task._sync_remote_source(
        spring_client, "ods_user", "user", ("id", "name")
    )

    assert changed is False
    assert partitions == set()


# 单页写入失败时抛出异常且不推进水位
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


# 按日志月份把脏数据聚合为 202609 与 202610 两个分区
@pytest.mark.anyio
async def test_collect_dirty_partitions_groups_by_month() -> None:
    items = [
        {"created_at": "2026-09-01 10:00:00"},
        {"created_at": "2026-09-30 23:59:59"},
        {"created_at": "2026-10-01 00:00:00"},
    ]
    partitions = task._collect_dirty_partitions("ods_article_log", items)
    assert partitions == {"202609", "202610"}


# 未登记日期字段的源表不产生脏分区
@pytest.mark.anyio
async def test_collect_dirty_partitions_ignores_unregistered_source() -> None:
    # ods_articles 不在 SOURCE_DIRTY_DATE_FIELD 中，不产生脏分区
    items = [{"update_at": "2026-09-01 10:00:00"}]
    assert task._collect_dirty_partitions("ods_articles", items) == set()


# 空值与非法日期不产生脏分区
@pytest.mark.anyio
async def test_collect_dirty_partitions_skips_invalid_dates() -> None:
    items = [
        {"created_at": None},
        {"created_at": "not-a-date"},
    ]
    assert task._collect_dirty_partitions("ods_article_log", items) == set()


# 脏分区对 6 张分区表各执行一次 DROP 与一次 INSERT
@pytest.mark.anyio
async def test_refresh_partitions_rebuilds_each_dirty_partition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executed = []

    async def fake_execute(sql: str, parameters: dict | None = None) -> None:
        executed.append((sql, parameters))

    monkeypatch.setattr(task, "execute_clickhouse_sql", fake_execute)

    await task._refresh_partitions({"202609"})

    # 6 张分区表，每张对 202609 分区执行一次 DROP + 一次 INSERT
    drop_calls = [c for c in executed if "DROP PARTITION" in c[0]]
    insert_calls = [c for c in executed if "INSERT" in c[0]]
    assert len(drop_calls) == 6
    assert len(insert_calls) == 6
    assert all(call[0].endswith("202609") for call in drop_calls)
    assert all(call[1] == {"partition": "202609"} for call in insert_calls)


# 分区刷新按 6 张表的依赖顺序依次执行
@pytest.mark.anyio
async def test_refresh_partitions_preserves_dependency_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    table_order: list[str] = []

    async def fake_execute(sql: str, parameters: dict | None = None) -> None:
        if "DROP PARTITION" in sql:
            # 从 ALTER TABLE warehouse.<table> DROP PARTITION 中提取表名
            table_order.append(sql.split(".")[1].split(" ")[0])

    monkeypatch.setattr(task, "execute_clickhouse_sql", fake_execute)

    await task._refresh_partitions({"202609"})

    expected = [
        "dwd_user_action",
        "dwd_api_call",
        "dws_article_day",
        "dws_user_day",
        "dws_api_day",
        "ads_user_day",
    ]
    assert table_order == expected


# 某表分区缺失导致 DROP 报错时不中断其余 6 张表的 INSERT
@pytest.mark.anyio
async def test_refresh_partitions_continues_when_partition_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 某张表没有该分区时 DROP 会报错，不应中断后续表的刷新
    inserted: list[tuple[str, dict | None]] = []

    async def fake_execute(sql: str, parameters: dict | None = None) -> None:
        if "DROP PARTITION" in sql:
            raise RuntimeError("partition not found")
        inserted.append((sql, parameters))

    monkeypatch.setattr(task, "execute_clickhouse_sql", fake_execute)

    await task._refresh_partitions({"202609"})

    # 6 张分区表的 INSERT 仍全部执行
    assert len(inserted) == 6
    assert all(call[1] == {"partition": "202609"} for call in inserted)


# 各源均无变更且无脏分区时不触发数仓刷新
@pytest.mark.anyio
async def test_sync_warehouse_skips_refresh_when_nothing_changed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spring_client = AsyncMock()
    # 8 个远端源都无新增数据，既无脏分区也无快照变更
    monkeypatch.setattr(
        task, "_sync_remote_source", AsyncMock(return_value=(False, set()))
    )
    monkeypatch.setattr(task, "create_warehouse_tables_async", AsyncMock())
    monkeypatch.setattr(task, "_sync_article_logs", AsyncMock(return_value=set()))
    monkeypatch.setattr(task, "_sync_api_logs", AsyncMock(return_value=set()))
    refresh = AsyncMock()
    monkeypatch.setattr(task, "_refresh_warehouse", refresh)

    await task._sync_warehouse(spring_client, AsyncMock())

    refresh.assert_not_awaited()


# 存在脏分区时按分区刷新且不刷新快照表
@pytest.mark.anyio
async def test_sync_warehouse_refreshes_when_dirty_partitions_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spring_client = AsyncMock()
    monkeypatch.setattr(
        task,
        "_sync_remote_source",
        AsyncMock(return_value=(False, {"202609"})),
    )
    monkeypatch.setattr(task, "create_warehouse_tables_async", AsyncMock())
    monkeypatch.setattr(task, "_sync_article_logs", AsyncMock(return_value=set()))
    monkeypatch.setattr(task, "_sync_api_logs", AsyncMock(return_value=set()))
    refresh = AsyncMock()
    monkeypatch.setattr(task, "_refresh_warehouse", refresh)

    await task._sync_warehouse(spring_client, AsyncMock())

    refresh.assert_awaited_once_with({"202609"}, False)


# MySQL 源有变更时即使无脏分区也刷新快照表
@pytest.mark.anyio
async def test_sync_warehouse_refreshes_snapshots_when_mysql_source_changed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # MySQL 源表只影响快照表，没有脏分区也必须刷新
    spring_client = AsyncMock()
    monkeypatch.setattr(
        task, "_sync_remote_source", AsyncMock(return_value=(True, set()))
    )
    monkeypatch.setattr(task, "create_warehouse_tables_async", AsyncMock())
    monkeypatch.setattr(task, "_sync_article_logs", AsyncMock(return_value=set()))
    monkeypatch.setattr(task, "_sync_api_logs", AsyncMock(return_value=set()))
    refresh = AsyncMock()
    monkeypatch.setattr(task, "_refresh_warehouse", refresh)

    await task._sync_warehouse(spring_client, AsyncMock())

    refresh.assert_awaited_once_with(set(), True)


# 仅事件分区变更时只刷分区不刷全量快照表
@pytest.mark.anyio
async def test_refresh_warehouse_skips_snapshots_when_only_events_changed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    full = AsyncMock()
    partitions = AsyncMock()
    monkeypatch.setattr(task, "_refresh_full_tables", full)
    monkeypatch.setattr(task, "_refresh_partitions", partitions)

    await task._refresh_warehouse({"202609"}, False)

    full.assert_not_awaited()
    partitions.assert_awaited_once_with({"202609"})
