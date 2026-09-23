from collections.abc import Mapping
from typing import Any

from clickhouse_sqlalchemy import engines
from sqlalchemy import func, literal_column

from app.core.db import ClickHouseBase


class WarehouseModel(ClickHouseBase):
    """数仓模型基类，不参与表创建"""

    __abstract__ = True
    __table_args__ = {"schema": "warehouse"}


def _monthly_partition(column: str) -> Any:
    """
    生成按月分区的表达式 toYYYYMM(column)

    partition_by 不接受字符串：clickhouse_sqlalchemy 会把字符串当作列名去元数据里查找，
    找不到直接抛 ConstraintColumnNotFoundError，因此必须传已绑定的 SQL 表达式
    literal_column 无需表对象即可构造，便于在静态配置中声明
    """
    return func.toYYYYMM(literal_column(column))


"""
ClickHouse 的 ENGINE/ORDER BY/partition_by 不是标准 SQLAlchemy 表参数，统一在元数据
注册完成后补充，既可保持模型定义简洁，也能让 metadata.create_all 生成正确 DDL

分区策略：仅对随时间持续累积、且查询常带时间范围的事实表按月分区
维度表（dim_*）、贴源表（ods_*）与快照表（ads_* 中的全量快照）数据量小且需全量保留，不分区
"""
WAREHOUSE_ENGINE_CONFIG: Mapping[str, tuple[type[Any], dict[str, Any]]] = {
    "sync_watermark": (
        engines.ReplacingMergeTree,
        {"version": "updated_at", "order_by": "table_name"},
    ),
    "ods_articles": (
        engines.ReplacingMergeTree,
        {"version": "update_at", "order_by": "id"},
    ),
    "ods_user": (
        engines.ReplacingMergeTree,
        {"version": "update_at", "order_by": "id"},
    ),
    "ods_category": (
        engines.ReplacingMergeTree,
        {"version": "update_time", "order_by": "id"},
    ),
    "ods_sub_category": (
        engines.ReplacingMergeTree,
        {"version": "update_time", "order_by": "id"},
    ),
    "ods_likes": (
        engines.ReplacingMergeTree,
        {"version": "created_time", "order_by": "id"},
    ),
    "ods_collects": (
        engines.ReplacingMergeTree,
        {"version": "created_time", "order_by": "id"},
    ),
    "ods_comments": (
        engines.ReplacingMergeTree,
        {"version": "update_time", "order_by": "id"},
    ),
    "ods_focus": (
        engines.ReplacingMergeTree,
        {"version": "created_time", "order_by": "id"},
    ),
    "ods_article_log": (
        engines.ReplacingMergeTree,
        {"version": "created_at", "order_by": "event_id"},
    ),
    "ods_api_log": (
        engines.ReplacingMergeTree,
        {"version": "created_at", "order_by": "event_id"},
    ),
    "dim_user": (
        engines.ReplacingMergeTree,
        {"version": "update_at", "order_by": "id"},
    ),
    "dim_category": (
        engines.ReplacingMergeTree,
        {"version": "update_time", "order_by": "sub_category_id"},
    ),
    "dwd_article_event": (
        engines.ReplacingMergeTree,
        {
            "version": "update_at",
            "order_by": "id",
            "partition_by": _monthly_partition("create_date"),
        },
    ),
    "dwd_user_action": (
        engines.ReplacingMergeTree,
        {
            "version": "action_time",
            "order_by": "event_id",
            "partition_by": _monthly_partition("action_date"),
        },
    ),
    "dwd_api_call": (
        engines.ReplacingMergeTree,
        {
            "version": "action_time",
            "order_by": "event_id",
            "partition_by": _monthly_partition("action_date"),
        },
    ),
    "dws_article_day": (
        engines.MergeTree,
        {
            "order_by": ("stat_date", "article_id"),
            "partition_by": _monthly_partition("stat_date"),
        },
    ),
    "dws_user_day": (
        engines.MergeTree,
        {
            "order_by": ("stat_date", "user_id"),
            "partition_by": _monthly_partition("stat_date"),
        },
    ),
    "dws_api_day": (
        engines.MergeTree,
        {
            "order_by": ("action_date", "api_path", "api_method", "api_description"),
            "partition_by": _monthly_partition("action_date"),
        },
    ),
    "ads_user_day": (
        engines.ReplacingMergeTree,
        {
            "version": "stat_time",
            "order_by": ("stat_date", "user_id"),
            "partition_by": _monthly_partition("stat_date"),
        },
    ),
    "ads_user_view_articles": (
        engines.ReplacingMergeTree,
        {"version": "stat_time", "order_by": ("user_id", "article_id")},
    ),
    "ads_user_stats": (
        engines.ReplacingMergeTree,
        {"version": "stat_time", "order_by": "user_id"},
    ),
    "ads_top10_articles": (
        engines.ReplacingMergeTree,
        {"version": "stat_time", "order_by": "id"},
    ),
    "ads_category_stats": (
        engines.ReplacingMergeTree,
        {"version": "stat_time", "order_by": "parent_category_id"},
    ),
    "ads_monthly_publish": (
        engines.ReplacingMergeTree,
        {"version": "stat_time", "order_by": "year_month"},
    ),
    "ads_platform_stats": (
        engines.ReplacingMergeTree,
        {"version": "stat_time", "order_by": "id"},
    ),
    "ads_api_average_speed": (
        engines.ReplacingMergeTree,
        {
            "version": "stat_time",
            "order_by": ("api_path", "api_method", "api_description"),
        },
    ),
    "ads_api_called_count": (
        engines.ReplacingMergeTree,
        {
            "version": "stat_time",
            "order_by": ("api_path", "api_method", "api_description"),
        },
    ),
    "ads_search_keywords": (
        engines.ReplacingMergeTree,
        {"version": "stat_time", "order_by": "keyword"},
    ),
}


def configure_warehouse_engines(metadata: Any) -> None:
    """为已导入的数仓模型附加 ClickHouse ENGINE 定义"""

    for table_name, (engine_type, options) in WAREHOUSE_ENGINE_CONFIG.items():
        table = metadata.tables.get(f"warehouse.{table_name}")
        if table is not None and not hasattr(table, "engine"):
            engine = engine_type(**options)
            engine._set_parent(table)
