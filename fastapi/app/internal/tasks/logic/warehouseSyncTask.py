import asyncio
import json
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Sequence

from app.core.base import Logger
from app.core.constants import Messages, RedisKeys, WarehouseScripts
from app.core.db import get_clickhouse_connection_pool, get_redis_client
from app.internal.clients import NestjsClient, SpringClient


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


async def _read_watermark(conn: Any, table_name: str) -> datetime:
    rows = await asyncio.to_thread(
        conn.execute, WarehouseScripts.WATERMARK_SELECT, {"table_name": table_name}
    )
    return (
        _parse_watermark(str(rows[0][0])) if rows else WarehouseScripts.EPOCH_DATETIME
    )


async def _write_watermark(conn: Any, table_name: str, value: datetime) -> None:
    await asyncio.to_thread(
        conn.execute,
        WarehouseScripts.WATERMARK_UPSERT,
        [(table_name, _format_watermark(value), datetime.now())],
    )


def _normalize_row(item: Dict[str, Any], columns: Sequence[str]) -> tuple[Any, ...]:
    row: list[Any] = []
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
        row.append(value)
    return tuple(row)


async def _sync_remote_source(
    spring_client: SpringClient,
    table_name: str,
    resource: str,
    columns: Sequence[str],
) -> None:
    conn: Any = None
    total = 0
    try:
        conn = await get_clickhouse_connection_pool().get_connection_async()
        watermark = await _read_watermark(conn, table_name)
        page_number = 1
        upper_watermark = watermark
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
            await asyncio.to_thread(
                conn.execute,
                f"INSERT INTO warehouse.{table_name} ({', '.join(columns)}) VALUES",
                rows,
            )
            total += len(rows)
            upper_watermark = max(
                upper_watermark, _to_datetime(page.get("upperWatermark"))
            )
            if not page.get("hasMore", False):
                break
            page_number += 1
        if upper_watermark > watermark:
            await _write_watermark(conn, table_name, upper_watermark)
        Logger.info(Messages.WAREHOUSE_ODS_SYNC_SUCCESS(table_name, total))
    finally:
        if conn:
            await get_clickhouse_connection_pool().return_connection_async(conn)


async def _sync_article_logs(conn: Any, nestjs_client: NestjsClient) -> None:
    last_cursor_rows = await asyncio.to_thread(
        conn.execute,
        WarehouseScripts.WATERMARK_SELECT,
        {"table_name": WarehouseScripts.ODS_ARTICLE_LOG_TABLE},
    )
    stored_cursor = str(last_cursor_rows[0][0]) if last_cursor_rows else ""
    cursor = stored_cursor if _is_mongo_cursor(stored_cursor) else ""
    while True:
        page = await nestjs_client.sync_article_logs(
            cursor, WarehouseScripts.ARTICLE_LOG_BATCH_SIZE
        )
        items = page.get("list", []) if isinstance(page, dict) else []
        if not items:
            break
        rows = [
            (
                str(item.get("_id") or item.get("id") or ""),
                int(item.get("userId") or item.get("user_id") or 0),
                int(item.get("articleId") or item.get("article_id") or 0),
                str(item.get("action") or ""),
                json.dumps(
                    item.get("content") or {}, ensure_ascii=False, default=str
                ),
                _to_datetime(item.get("createdAt") or item.get("created_at")),
            )
            for item in items
        ]
        await asyncio.to_thread(
            conn.execute, WarehouseScripts.ODS_ARTICLE_LOG_INSERT, rows
        )
        next_cursor = page.get("nextCursor") or page.get("next_cursor")
        if next_cursor:
            cursor = next_cursor
        else:
            cursor = rows[-1][0]
            break
    if cursor:
        await asyncio.to_thread(
            conn.execute,
            WarehouseScripts.WATERMARK_UPSERT,
            [(WarehouseScripts.ODS_ARTICLE_LOG_TABLE, cursor, datetime.now())],
        )


async def _refresh_warehouse(conn: Any) -> None:
    for sql in WarehouseScripts.REFRESH_DERIVED_TABLES:
        await asyncio.to_thread(conn.execute, sql)
    for sql in (
        WarehouseScripts.REFRESH_DIM_USER,
        WarehouseScripts.REFRESH_DIM_CATEGORY,
        WarehouseScripts.REFRESH_DWD_ARTICLE,
        WarehouseScripts.REFRESH_DWD_ACTION,
        WarehouseScripts.REFRESH_DWS_ARTICLE,
        WarehouseScripts.REFRESH_DWS_USER,
        *WarehouseScripts.REFRESH_ADS,
        WarehouseScripts.REFRESH_ADS_USER_DAY,
        WarehouseScripts.REFRESH_ADS_USER_VIEW_ARTICLES,
        WarehouseScripts.REFRESH_ADS_USER_STATS,
    ):
        await asyncio.to_thread(conn.execute, sql)


async def _sync_warehouse(
    spring_client: SpringClient, nestjs_client: Optional[NestjsClient] = None
) -> None:
    await asyncio.gather(
        *(
            _sync_remote_source(spring_client, *source)
            for source in WarehouseScripts.REMOTE_SOURCES
        )
    )
    conn: Any = None
    try:
        conn = await get_clickhouse_connection_pool().get_connection_async()
        if nestjs_client:
            await _sync_article_logs(conn, nestjs_client)
        await _refresh_warehouse(conn)
        Logger.info(Messages.WAREHOUSE_REFRESH_SUCCESS)
    except Exception as error:
        Logger.error(Messages.WAREHOUSE_REFRESH_FAILED(error))
        Logger.debug(traceback.format_exc())
    finally:
        if conn:
            await get_clickhouse_connection_pool().return_connection_async(conn)


async def sync_warehouse_async(
    spring_client: Optional[SpringClient] = None,
    nestjs_client: Optional[NestjsClient] = None,
) -> None:
    """通过 Spring/Nest 内部接口同步 ODS 并刷新数仓"""
    if spring_client is None:
        return
    redis_client = get_redis_client()
    lock_value = await redis_client.try_lock(
        RedisKeys.LOCK_TASK_WAREHOUSE, RedisKeys.LOCK_TASK_WAREHOUSE_EXPIRE
    )
    if lock_value is None:
        Logger.info(Messages.WAREHOUSE_LOCK_NOT_ACQUIRED)
        return
    try:
        await _sync_warehouse(spring_client, nestjs_client)
    finally:
        await redis_client.unlock(RedisKeys.LOCK_TASK_WAREHOUSE, lock_value)
