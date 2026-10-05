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
    monkeypatch.setattr(
        task, "_sync_article_logs", AsyncMock(return_value=(False, set()))
    )
    monkeypatch.setattr(task, "_sync_api_logs", AsyncMock(return_value=(False, set())))
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
    monkeypatch.setattr(
        task, "_sync_article_logs", AsyncMock(return_value=(False, set()))
    )
    monkeypatch.setattr(task, "_sync_api_logs", AsyncMock(return_value=(False, set())))
    refresh = AsyncMock()
    monkeypatch.setattr(task, "_refresh_warehouse", refresh)

    await task._sync_warehouse(spring_client, AsyncMock())

    refresh.assert_awaited_once_with({"202609"}, set())


# MySQL 源有变更时即使无脏分区也按变更源表刷新快照表
@pytest.mark.anyio
async def test_sync_warehouse_refreshes_snapshots_when_mysql_source_changed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # MySQL 源表只影响快照表，没有脏分区也必须刷新，且只登记本次有增量的源表
    spring_client = AsyncMock()

    async def fake_remote_source(
        spring_client: object, table_name: str, resource: str, columns: tuple[str, ...]
    ) -> tuple[bool, set[str]]:
        return (table_name == "ods_user", set())

    monkeypatch.setattr(task, "_sync_remote_source", fake_remote_source)
    monkeypatch.setattr(task, "create_warehouse_tables_async", AsyncMock())
    monkeypatch.setattr(
        task, "_sync_article_logs", AsyncMock(return_value=(False, set()))
    )
    monkeypatch.setattr(task, "_sync_api_logs", AsyncMock(return_value=(False, set())))
    refresh = AsyncMock()
    monkeypatch.setattr(task, "_refresh_warehouse", refresh)

    await task._sync_warehouse(spring_client, AsyncMock())

    refresh.assert_awaited_once_with(set(), {"ods_user"})


# 源表映射到快照表的闭包只保留受影响的表
def test_resolve_affected_snapshots_filters_unrelated_tables() -> None:
    assert task._resolve_affected_snapshots({"ods_user"}) == {
        "dim_user",
        "ads_top10_articles",
        "ads_user_stats",
    }


# 变更经由分区表传导到依赖分区表结果的 ADS 快照表
def test_resolve_affected_snapshots_propagates_through_partitioned_tables() -> None:
    assert task._resolve_affected_snapshots({"ods_api_log"}) == {
        "ads_api_average_speed",
        "ads_api_called_count",
    }


# 无对应下游的源表不产生任何快照表重建
def test_resolve_affected_snapshots_ignores_unknown_source() -> None:
    assert task._resolve_affected_snapshots({"ods_unknown"}) == set()


# 仅点赞变更时只重建依赖 dwd_user_action 的 ADS 快照表
@pytest.mark.anyio
async def test_refresh_warehouse_rebuilds_only_affected_snapshots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executed: list[str] = []

    async def fake_execute(sql: str, parameters: dict | None = None) -> None:
        executed.append(sql)

    monkeypatch.setattr(task, "execute_clickhouse_sql", fake_execute)

    await task._refresh_warehouse(set(), {"ods_likes"})

    assert [sql for sql in executed if sql.startswith("TRUNCATE")] == [
        "TRUNCATE TABLE warehouse.ads_platform_stats",
        "TRUNCATE TABLE warehouse.ads_user_view_articles",
        "TRUNCATE TABLE warehouse.ads_user_stats",
    ]


# 上游维度变更沿依赖链级联重建，未受影响的快照表不动
@pytest.mark.anyio
async def test_refresh_warehouse_cascades_through_dependency_chain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executed: list[str] = []

    async def fake_execute(sql: str, parameters: dict | None = None) -> None:
        executed.append(sql)

    monkeypatch.setattr(task, "execute_clickhouse_sql", fake_execute)

    await task._refresh_warehouse(set(), {"ods_sub_category"})

    truncated = [sql for sql in executed if sql.startswith("TRUNCATE")]
    assert "TRUNCATE TABLE warehouse.dim_category" in truncated
    assert "TRUNCATE TABLE warehouse.dwd_article_event" in truncated
    assert "TRUNCATE TABLE warehouse.ads_category_stats" in truncated
    assert "TRUNCATE TABLE warehouse.ads_user_stats" in truncated
    assert "TRUNCATE TABLE warehouse.dim_user" not in truncated
    assert "TRUNCATE TABLE warehouse.ads_api_average_speed" not in truncated
    assert "TRUNCATE TABLE warehouse.ads_search_keywords" not in truncated


# 分区表刷新固定夹在上游与下游快照表之间
@pytest.mark.anyio
async def test_refresh_warehouse_orders_snapshots_around_partitions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order: list[str] = []
    captured: list[tuple[tuple[tuple[str, str], ...], set[str]]] = []

    async def fake_snapshot(
        steps: tuple[tuple[str, str], ...], affected: set[str]
    ) -> None:
        captured.append((steps, affected))
        order.append("snapshot")

    async def fake_partitions(dirty_partitions: set[str]) -> None:
        order.append("partitions")

    monkeypatch.setattr(task, "_refresh_snapshot_tables", fake_snapshot)
    monkeypatch.setattr(task, "_refresh_partitions", fake_partitions)

    await task._refresh_warehouse({"202609"}, {"ods_likes"})

    assert order == ["snapshot", "partitions", "snapshot"]
    assert captured[0][0] == task.WarehouseScripts.UPSTREAM_SNAPSHOT_STEPS
    assert captured[1][0] == task.WarehouseScripts.DOWNSTREAM_SNAPSHOT_STEPS
    assert (
        captured[0][1]
        == captured[1][1]
        == {
            "ads_platform_stats",
            "ads_user_view_articles",
            "ads_user_stats",
        }
    )


# 指定资源时只同步该源表，实现表粒度精确同步
@pytest.mark.anyio
async def test_sync_warehouse_filters_sources_by_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    synced: list[str] = []

    async def fake_remote_source(
        spring_client: object, table_name: str, resource: str, columns: tuple[str, ...]
    ) -> tuple[bool, set[str]]:
        synced.append(resource)
        return (False, set())

    monkeypatch.setattr(task, "create_warehouse_tables_async", AsyncMock())
    monkeypatch.setattr(task, "_sync_remote_source", fake_remote_source)

    await task._sync_warehouse(AsyncMock(), None, {"articles"})

    assert synced == ["articles"]


# 日志表只由全量同步刷新，实时事件触发时跳过
def test_should_sync_log_sources() -> None:
    assert task._should_sync_log_sources(None) is True
    assert task._should_sync_log_sources({"articles"}) is False
    assert task._should_sync_log_sources({"comments"}) is False
    assert task._should_sync_log_sources({"category"}) is False


# 数仓同步按资源名透传到同步函数
@pytest.mark.anyio
async def test_sync_warehouse_async_forwards_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedisClient()
    sync = AsyncMock()
    monkeypatch.setattr(task, "get_redis_client", lambda: redis_client)
    monkeypatch.setattr(task, "_sync_warehouse", sync)

    await task.sync_warehouse_async(AsyncMock(), None, ["comments"])

    sync.assert_awaited_once()
    assert sync.await_args.args[2] == {"comments"}
