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
) -> None:
    total = 0
    watermark = await _read_watermark(table_name)
    page_number = 1
    upper_watermark = watermark
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
        total += len(rows)
        upper_watermark = max(upper_watermark, _to_datetime(page.get("upperWatermark")))
        if not page.get("hasMore", False):
            break
        page_number += 1
    if upper_watermark > watermark:
        await _write_watermark(table_name, upper_watermark)
    Logger.info(Messages.WAREHOUSE_ODS_SYNC_SUCCESS(table_name, total))


async def _sync_api_logs(nestjs_client: NestjsClient) -> None:
    """按 MongoDB ID 游标增量同步 NestJS API 日志到 ClickHouse ODS 层"""
    stored_cursor = await _read_watermark_value(WarehouseScripts.ODS_API_LOG_TABLE)
    cursor = stored_cursor if _is_mongo_cursor(stored_cursor) else ""
    total = 0
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


async def _sync_article_logs(nestjs_client: NestjsClient) -> None:
    stored_cursor = await _read_watermark_value(WarehouseScripts.ODS_ARTICLE_LOG_TABLE)
    cursor = stored_cursor if _is_mongo_cursor(stored_cursor) else ""
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
                "article_id": int(
                    item.get("articleId") or item.get("article_id") or 0
                ),
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
        next_cursor = page.get("nextCursor") or page.get("next_cursor")
        if next_cursor:
            cursor = next_cursor
        else:
            cursor = str(rows[-1]["event_id"])
            break
    if cursor:
        await _write_watermark_value(WarehouseScripts.ODS_ARTICLE_LOG_TABLE, cursor)


async def _refresh_warehouse() -> None:
    for sql in WarehouseScripts.REFRESH_DERIVED_TABLES:
        await execute_clickhouse_sql(sql)
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
        WarehouseScripts.REFRESH_DWD_API_CALL,
        WarehouseScripts.REFRESH_DWS_API_DAY,
        *WarehouseScripts.REFRESH_ADS_API,
        WarehouseScripts.REFRESH_ADS_SEARCH_KEYWORDS,
    ):
        await execute_clickhouse_sql(sql)


async def _sync_warehouse(
    spring_client: SpringClient, nestjs_client: Optional[NestjsClient] = None
) -> None:
    await create_warehouse_tables_async()
    await asyncio.gather(
        *(
            _sync_remote_source(spring_client, *source)
            for source in WarehouseScripts.REMOTE_SOURCES
        )
    )
    try:
        if nestjs_client:
            await _sync_article_logs(nestjs_client)
            await _sync_api_logs(nestjs_client)
        await _refresh_warehouse()
        Logger.info(Messages.WAREHOUSE_REFRESH_SUCCESS)
    except Exception as error:
        Logger.error(Messages.WAREHOUSE_REFRESH_FAILED(error))
        Logger.debug(traceback.format_exc())


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
