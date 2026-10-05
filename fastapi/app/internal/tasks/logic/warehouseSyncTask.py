import asyncio
import json
import traceback
from collections.abc import Sequence
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import desc, insert, select

from app.core.base import Logger
from app.core.constants import Messages, RedisKeys, WarehouseScripts
from app.core.db import (
    clickhouse_async_engine,
    create_warehouse_tables_async,
    execute_clickhouse_sql,
    get_redis_client,
)
from app.internal.clients import NestjsClient, SpringClient
from app.internal.models import (
    OdsApiLog,
    OdsArticle,
    OdsArticleLog,
    OdsCategory,
    OdsCollect,
    OdsComment,
    OdsFocus,
    OdsLike,
    OdsSubCategory,
    OdsUser,
    SyncWatermark,
)

REMOTE_MODELS: dict[str, type[Any]] = {
    "ods_articles": OdsArticle,
    "ods_user": OdsUser,
    "ods_category": OdsCategory,
    "ods_sub_category": OdsSubCategory,
    "ods_likes": OdsLike,
    "ods_collects": OdsCollect,
    "ods_comments": OdsComment,
    "ods_focus": OdsFocus,
}

def _should_sync_log_sources(resources: Optional[set[str]]) -> bool:
    """
    日志表仅由全量同步刷新

    ods_article_log 与 ods_api_log 的数据源头是 MQ 异步链路加 NestJS 攒批落库，
    实时触发时新日志往往尚未落到 MongoDB，逐次拉取既拉不到最新数据又放大调用量，
    因此统一交给定时任务（每 10 分钟）与手动全量触发处理
    """
    return not resources


def _parse_watermark(value: Optional[str]) -> datetime:
    if not value:
        return WarehouseScripts.EPOCH_DATETIME
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return WarehouseScripts.EPOCH_DATETIME


def _format_watermark(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _to_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if value is None:
        return WarehouseScripts.EPOCH_DATETIME
    return _parse_watermark(str(value))


def _is_mongo_cursor(value: Any) -> bool:
    cursor = str(value or "")
    return len(cursor) == 24 and all(
        character in "0123456789abcdefABCDEF" for character in cursor
    )


async def _read_watermark(table_name: str) -> datetime:
    value = await _read_watermark_value(table_name)
    return _parse_watermark(value) if value else WarehouseScripts.EPOCH_DATETIME


async def _read_watermark_value(table_name: str) -> str:
    # ReplacingMergeTree 后台合并前可能同时存在新旧水位，按更新时间取最新一行
    statement = (
        select(SyncWatermark.last_watermark)
        .where(SyncWatermark.table_name == table_name)
        .order_by(desc(SyncWatermark.updated_at))
        .limit(1)
    )
    async with clickhouse_async_engine.connect() as connection:
        result = await connection.execute(statement)
        value = result.scalar_one_or_none()
    return str(value or "")


async def _write_watermark(table_name: str, value: datetime) -> None:
    await _write_watermark_value(table_name, _format_watermark(value))


async def _write_watermark_value(table_name: str, value: str) -> None:
    # ClickHouse 没有行级 UPSERT，先清理同一张源表的旧水位，再插入唯一新水位
    await execute_clickhouse_sql(
        WarehouseScripts.WATERMARK_DELETE_BY_TABLE,
        {"table_name": table_name},
    )
    async with clickhouse_async_engine.connect() as connection:
        await connection.execute(
            insert(SyncWatermark),
            {
                "table_name": table_name,
                "last_watermark": value,
                "updated_at": datetime.now(),
            },
        )


async def _insert_rows(model: type[Any], rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    async with clickhouse_async_engine.connect() as connection:
        await connection.execute(insert(model), rows)


def _collect_dirty_partitions(table_name: str, items: list[dict[str, Any]]) -> set[str]:
    """
    从同步的原始行中推导受影响的月份分区

    只对登记在 SOURCE_DIRTY_DATE_FIELD 的源表生效，返回形如 {"202609"} 的分区值集合
    """
    date_field = WarehouseScripts.SOURCE_DIRTY_DATE_FIELD.get(table_name)
    if not date_field:
        return set()
    partitions: set[str] = set()
    for item in items:
        value = item.get(date_field)
        if value is None:
            continue
        moment = _to_datetime(value)
        if moment == WarehouseScripts.EPOCH_DATETIME:
            continue
        partitions.add(moment.strftime("%Y%m"))
    return partitions


def _normalize_row(item: dict[str, Any], columns: Sequence[str]) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for column in columns:
        value = item.get(column)
        if column in WarehouseScripts.DATETIME_COLUMNS:
            value = _to_datetime(value)
        elif column in WarehouseScripts.STRING_COLUMNS:
            value = str(value or "")
        elif column in WarehouseScripts.FLOAT_COLUMNS:
            value = float(value or 0.0)
        elif column in WarehouseScripts.INTEGER_COLUMNS:
            value = int(value or 0)
        row[column] = value
    return row


async def _sync_remote_source(
    spring_client: SpringClient,
    table_name: str,
    resource: str,
    columns: Sequence[str],
) -> tuple[bool, set[str]]:
    """
    增量同步一张远端源表到 ODS

    返回 (本次是否有新数据, 受影响的分区值集合)
    MySQL 源表只服务于全量快照表（dim_*、dwd_article_event），不产生脏分区，
    因此需要单独返回是否有变更，避免快照表漏刷新
    """
    total = 0
    watermark = await _read_watermark(table_name)
    page_number = 1
    upper_watermark = watermark
    dirty_partitions: set[str] = set()
    model = REMOTE_MODELS[table_name]
    while True:
        page = await spring_client.sync_warehouse_data(
            resource,
            _format_watermark(watermark),
            page_number,
            WarehouseScripts.BATCH_SIZE,
        )
        items = page.get("list", []) if isinstance(page, dict) else []
        if not items:
            break
        rows = [_normalize_row(item, columns) for item in items]
        await _insert_rows(model, rows)
        dirty_partitions |= _collect_dirty_partitions(table_name, items)
        total += len(rows)
        upper_watermark = max(upper_watermark, _to_datetime(page.get("upperWatermark")))
        if not page.get("hasMore", False):
            break
        page_number += 1
    if upper_watermark > watermark:
        await _write_watermark(table_name, upper_watermark)
    Logger.info(Messages.WAREHOUSE_ODS_SYNC_SUCCESS(table_name, total))
    return total > 0, dirty_partitions


async def _sync_api_logs(nestjs_client: NestjsClient) -> tuple[bool, set[str]]:
    """按 MongoDB ID 游标增量同步 NestJS API 日志到 ClickHouse ODS 层

    返回 (本次是否有新数据, 受影响的分区值集合)
    """
    stored_cursor = await _read_watermark_value(WarehouseScripts.ODS_API_LOG_TABLE)
    cursor = stored_cursor if _is_mongo_cursor(stored_cursor) else ""
    total = 0
    dirty_partitions: set[str] = set()
    while True:
        page = await nestjs_client.sync_api_logs(
            cursor, WarehouseScripts.ARTICLE_LOG_BATCH_SIZE
        )
        items = page.get("list", []) if isinstance(page, dict) else []
        if not items:
            break
        rows = [
            {
                "event_id": str(item.get("_id") or item.get("id") or ""),
                "user_id": int(item.get("userId") or item.get("user_id") or 0),
                "username": str(item.get("username") or ""),
                "api_description": str(
                    item.get("apiDescription") or item.get("api_description") or ""
                ),
                "api_path": str(item.get("apiPath") or item.get("api_path") or ""),
                "api_method": str(
                    item.get("apiMethod") or item.get("api_method") or ""
                ),
                "response_time": float(
                    item.get("responseTime") or item.get("response_time") or 0.0
                ),
                "created_at": _to_datetime(
                    item.get("createdAt") or item.get("created_at")
                ),
            }
            for item in items
        ]
        await _insert_rows(OdsApiLog, rows)
        dirty_partitions |= _collect_dirty_partitions(
            WarehouseScripts.ODS_API_LOG_TABLE, items
        )
        total += len(rows)
        next_cursor = page.get("nextCursor") or page.get("next_cursor")
        if next_cursor:
            cursor = next_cursor
        else:
            cursor = str(rows[-1]["event_id"])
            break
    if cursor:
        await _write_watermark_value(WarehouseScripts.ODS_API_LOG_TABLE, cursor)
    if total:
        Logger.info(
            Messages.WAREHOUSE_API_LOG_SYNC_SUCCESS(
                WarehouseScripts.ODS_API_LOG_TABLE, total
            )
        )
    return total > 0, dirty_partitions


async def _sync_article_logs(nestjs_client: NestjsClient) -> tuple[bool, set[str]]:
    """按 MongoDB ID 游标增量同步 NestJS 文章行为日志到 ODS 层

    返回 (本次是否有新数据, 受影响的分区值集合)
    """
    stored_cursor = await _read_watermark_value(WarehouseScripts.ODS_ARTICLE_LOG_TABLE)
    cursor = stored_cursor if _is_mongo_cursor(stored_cursor) else ""
    total = 0
    dirty_partitions: set[str] = set()
    while True:
        page = await nestjs_client.sync_article_logs(
            cursor, WarehouseScripts.ARTICLE_LOG_BATCH_SIZE
        )
        items = page.get("list", []) if isinstance(page, dict) else []
        if not items:
            break
        rows = [
            {
                "event_id": str(item.get("_id") or item.get("id") or ""),
                "user_id": int(item.get("userId") or item.get("user_id") or 0),
                "article_id": int(item.get("articleId") or item.get("article_id") or 0),
                "action": str(item.get("action") or ""),
                "content": json.dumps(
                    item.get("content") or {}, ensure_ascii=False, default=str
                ),
                "created_at": _to_datetime(
                    item.get("createdAt") or item.get("created_at")
                ),
            }
            for item in items
        ]
        await _insert_rows(OdsArticleLog, rows)
        dirty_partitions |= _collect_dirty_partitions(
            WarehouseScripts.ODS_ARTICLE_LOG_TABLE, items
        )
        total += len(rows)
        next_cursor = page.get("nextCursor") or page.get("next_cursor")
        if next_cursor:
            cursor = next_cursor
        else:
            cursor = str(rows[-1]["event_id"])
            break
    if cursor:
        await _write_watermark_value(WarehouseScripts.ODS_ARTICLE_LOG_TABLE, cursor)
    if total:
        Logger.info(
            Messages.WAREHOUSE_API_LOG_SYNC_SUCCESS(
                WarehouseScripts.ODS_ARTICLE_LOG_TABLE, total
            )
        )
    return total > 0, dirty_partitions


def _resolve_affected_snapshots(changed_sources: set[str]) -> set[str]:
    """
    按依赖图推导受影响的快照表集合

    源表变更先传播到依赖它的分区表（如 ods_likes -> dwd_user_action），
    再传播到依赖这些分区表的 ADS 快照表，因此需要做完整的闭包推导
    """
    affected: set[str] = set(changed_sources)
    dependencies_by_table: dict[str, frozenset[str]] = {
        **WarehouseScripts.PARTITIONED_DEPENDENCIES,
        **WarehouseScripts.SNAPSHOT_DEPENDENCIES,
    }
    changed = True
    while changed:
        changed = False
        for table_name, dependencies in dependencies_by_table.items():
            if table_name in affected:
                continue
            if dependencies & affected:
                affected.add(table_name)
                changed = True
    return affected & set(WarehouseScripts.SNAPSHOT_DEPENDENCIES)


async def _refresh_snapshot_tables(
    steps: Sequence[tuple[str, str]], affected: set[str]
) -> None:
    """重建受影响的快照表：清空后重新插入，未受影响的表直接跳过"""
    for table_name, refresh_sql in steps:
        if table_name not in affected:
            continue
        await execute_clickhouse_sql(WarehouseScripts.TRUNCATE_TEMPLATE % table_name)
        await execute_clickhouse_sql(refresh_sql)


async def _drop_partition_if_exists(table_name: str, partition: str) -> None:
    """
    删除分区，分区不存在时静默跳过

    ClickHouse 的 DROP PARTITION 在分区不存在时会报错，
    而脏分区来自全部源表的并集，某张表未必对所有脏分区都有数据（如首次运行或空表）
    """
    try:
        await execute_clickhouse_sql(
            WarehouseScripts.PARTITION_DROP_TEMPLATE % (table_name, partition)
        )
    except Exception as error:
        Logger.debug(
            Messages.WAREHOUSE_PARTITION_DROP_SKIPPED(table_name, partition, error)
        )


async def _refresh_partitions(dirty_partitions: set[str]) -> None:
    """
    按分区增量重建分区表

    对每个脏分区执行 DROP PARTITION 后重新插入，分区表按依赖顺序处理，
    上游分区（dwd）必须先于下游分区（dws/ads）重建
    """
    for table_name in WarehouseScripts.PARTITIONED_REFRESH_ORDER:
        refresh_sql, _ = WarehouseScripts.PARTITIONED_REFRESH_STEPS[table_name]
        for partition in sorted(dirty_partitions):
            await _drop_partition_if_exists(table_name, partition)
            await execute_clickhouse_sql(refresh_sql, {"partition": partition})


async def _refresh_warehouse(
    dirty_partitions: set[str], changed_sources: set[str]
) -> None:
    """
    刷新派生层

    执行顺序为「上游快照表 -> 分区表 -> 下游快照表」：
    分区表依赖 dim_*、dwd_article_event，而 ads_platform_stats、ads_user_stats 等
    又依赖分区表结果，因此上游快照表必须先重建，依赖分区表的下游快照表必须最后重建
    """
    affected_snapshots = _resolve_affected_snapshots(changed_sources)
    if affected_snapshots:
        Logger.info(Messages.WAREHOUSE_AFFECTED_SNAPSHOTS(sorted(affected_snapshots)))
    await _refresh_snapshot_tables(
        WarehouseScripts.UPSTREAM_SNAPSHOT_STEPS, affected_snapshots
    )
    if dirty_partitions:
        await _refresh_partitions(dirty_partitions)
    await _refresh_snapshot_tables(
        WarehouseScripts.DOWNSTREAM_SNAPSHOT_STEPS, affected_snapshots
    )


async def _sync_warehouse(
    spring_client: SpringClient,
    nestjs_client: Optional[NestjsClient] = None,
    resources: Optional[set[str]] = None,
) -> None:
    await create_warehouse_tables_async()
    # 按资源名收窄源表范围，实现表粒度精确同步
    sources = [
        source
        for source in WarehouseScripts.REMOTE_SOURCES
        if not resources or source[1] in resources
    ]
    source_results = await asyncio.gather(
        *(_sync_remote_source(spring_client, *source) for source in sources)
    )
    dirty_partitions: set[str] = set()
    changed_sources: set[str] = set()
    for (table_name, _, _), (changed, partitions) in zip(sources, source_results):
        if changed:
            changed_sources.add(table_name)
        dirty_partitions |= partitions
    try:
        if nestjs_client and _should_sync_log_sources(resources):
            article_log_result, api_log_result = await asyncio.gather(
                _sync_article_logs(nestjs_client),
                _sync_api_logs(nestjs_client),
            )
            event_changed, event_partitions = article_log_result
            api_changed, api_partitions = api_log_result
            if event_changed:
                changed_sources.add(WarehouseScripts.ODS_ARTICLE_LOG_TABLE)
            if api_changed:
                changed_sources.add(WarehouseScripts.ODS_API_LOG_TABLE)
            dirty_partitions |= event_partitions
            dirty_partitions |= api_partitions
        if dirty_partitions or changed_sources:
            if dirty_partitions:
                Logger.info(
                    Messages.WAREHOUSE_DIRTY_PARTITIONS(sorted(dirty_partitions))
                )
            await _refresh_warehouse(dirty_partitions, changed_sources)
        else:
            Logger.info(Messages.WAREHOUSE_REFRESH_SKIPPED)
        Logger.info(Messages.WAREHOUSE_REFRESH_SUCCESS)
    except Exception as error:
        Logger.error(Messages.WAREHOUSE_REFRESH_FAILED(error))
        Logger.debug(traceback.format_exc())


async def sync_warehouse_async(
    spring_client: Optional[SpringClient] = None,
    nestjs_client: Optional[NestjsClient] = None,
    resources: Optional[list[str]] = None,
) -> None:
    """通过 Spring/Nest 内部接口同步 ODS 并刷新数仓，可按资源名精确到表"""
    if spring_client is None:
        return
    resource_set: Optional[set[str]] = set(resources) if resources else None
    redis_client = get_redis_client()
    lock_value = await redis_client.try_lock(
        RedisKeys.LOCK_TASK_WAREHOUSE, RedisKeys.LOCK_TASK_WAREHOUSE_EXPIRE
    )
    if lock_value is None:
        Logger.info(Messages.WAREHOUSE_LOCK_NOT_ACQUIRED)
        return
    try:
        await _sync_warehouse(spring_client, nestjs_client, resource_set)
    finally:
        await redis_client.unlock(RedisKeys.LOCK_TASK_WAREHOUSE, lock_value)
