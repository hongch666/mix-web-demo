import asyncio
import time
import traceback
from functools import lru_cache
from typing import Any, Dict, List

from app.core.base import Logger
from app.core.config import load_config
from app.core.constants import Messages, Scripts
from app.core.db import ClickhouseConnectionPool, get_clickhouse_connection_pool


class ArticleMapper:
    """文章 Mapper"""

    def __init__(self) -> None:
        self._clickhouse_pool: ClickhouseConnectionPool = (
            get_clickhouse_connection_pool()
        )

    def _safe_convert_to_list_of_dicts(
        self, results: Any, columns: List[str]
    ) -> List[Dict[str, Any]]:
        """安全转换 ClickHouse 查询结果为字典列表"""
        result: List[Dict[str, Any]] = []
        for row in results:
            try:
                row_dict = {}
                for col, val in zip(columns, row):
                    # 安全转换值类型
                    try:
                        if val is None:
                            row_dict[col] = None
                        else:
                            row_dict[col] = val
                    except Exception as val_e:
                        Logger.debug(
                            Messages.CLICKHOUSE_VALUE_CONVERSION_FAILED(col, val, val_e)
                        )
                        row_dict[col] = None
                result.append(row_dict)
            except Exception as row_e:
                Logger.debug(Messages.CLICKHOUSE_ROW_CONVERSION_FAILED(row_e))
                continue
        return result

    async def get_top10_articles_clickhouse_mapper_async(
        self,
    ) -> List[Dict[str, Any]]:
        """获取前10篇文章 - ClickHouse 查表"""

        # ClickHouse 表中实际存在的字段（不包含 username）
        columns: List[str] = [
            "id",
            "title",
            "tags",
            "status",
            "views",
            "create_at",
            "update_at",
            "content",
            "user_id",
            "sub_category_id",
        ]

        start: float = time.time()
        # 从连接池获取连接
        pool_start: float = time.time()
        ch_conn: Any = self._clickhouse_pool.get_connection()
        pool_time: float = time.time() - pool_start

        # 查询 ClickHouse
        Logger.info(Messages.TOP10_CLICKHOUSE_QUERY)
        query_start: float = time.time()
        ch_table: str = load_config("database")["clickhouse"]["table"]
        query = Scripts.TOP10_ARTICLES_CLICKHOUSE_QUERY(", ".join(columns), ch_table)

        try:
            results: List[tuple] = await asyncio.to_thread(ch_conn.execute, query)
            query_time: float = time.time() - query_start

            # 安全转换为字典
            result: List[Dict[str, Any]] = self._safe_convert_to_list_of_dicts(
                results, columns
            )

            total_time: float = time.time() - start
            Logger.info(
                Messages.CLICKHOUSE_QUERY_TIMING(pool_time, query_time, total_time)
            )

            return result
        except AttributeError as ae:
            Logger.error(Messages.CLICKHOUSE_ATTR_ERROR(ae))
            Logger.error(Messages.CLICKHOUSE_DETAIL_ERROR(traceback.format_exc()))
            raise
        except Exception as e:
            Logger.error(Messages.CLICKHOUSE_DEGRADE_TO_DB(type(e).__name__, e))
            Logger.debug(Messages.CLICKHOUSE_DETAIL_EXCEPTION(traceback.format_exc()))
            raise
        finally:
            # 归还连接到池
            if ch_conn:
                self._clickhouse_pool.return_connection(ch_conn)

    async def get_clickhouse_connection_async(self) -> Any:
        """获取 ClickHouse 连接（用于缓存版本检查）"""
        return await asyncio.to_thread(self._clickhouse_pool.get_connection)

    async def return_clickhouse_connection_async(self, conn: Any) -> None:
        """归还 ClickHouse 连接"""
        await asyncio.to_thread(self._clickhouse_pool.return_connection, conn)

    async def get_category_article_count_clickhouse_mapper_async(
        self,
    ) -> List[Dict[str, Any]]:
        """
        从ClickHouse获取按父分类排序的文章数量
        """
        start: float = time.time()
        ch_conn: Any = self._clickhouse_pool.get_connection()

        Logger.info(Messages.CATEGORY_STATISTICS_CLICKHOUSE_QUERY)
        query_start: float = time.time()
        ch_table: str = load_config("database")["clickhouse"]["table"]
        query = Scripts.CATEGORY_ARTICLE_COUNT_CLICKHOUSE_QUERY(ch_table)

        try:
            results: Any = await asyncio.to_thread(ch_conn.execute, query)
            query_time: float = time.time() - query_start

            # 安全转换为字典列表
            result: List[Dict[str, Any]] = []
            for r in results:
                try:
                    result.append(
                        {
                            "sub_category_id": int(r[0]) if r[0] is not None else None,
                            "count": int(r[1]) if r[1] is not None else 0,
                        }
                    )
                except (ValueError, TypeError) as e:
                    Logger.debug(Messages.CLICKHOUSE_QUERY_ROW_CONVERSION_FAILED(e))
                    continue

            total_time: float = time.time() - start
            Logger.info(
                Messages.CLICKHOUSE_CATEGORY_QUERY_RESULT(
                    query_time, total_time, len(result)
                )
            )

            return result
        except AttributeError as ae:
            Logger.error(Messages.CLICKHOUSE_ATTR_ERROR(ae))
            Logger.error(Messages.CLICKHOUSE_DETAIL_ERROR(traceback.format_exc()))
            raise
        except Exception as e:
            Logger.error(Messages.CLICKHOUSE_DEGRADE_TO_DB(type(e).__name__, e))
            Logger.debug(Messages.CLICKHOUSE_DETAIL_EXCEPTION(traceback.format_exc()))
            raise
        finally:
            if ch_conn:
                self._clickhouse_pool.return_connection(ch_conn)

    async def get_monthly_publish_count_clickhouse_mapper_async(
        self,
    ) -> List[Dict[str, Any]]:
        """
        从ClickHouse获取最近24个月的文章发布数量统计（包含零值月份）
        说明: 返回的是过去24个月内有数据的月份，缺失月份由service层补零
        """
        start: float = time.time()
        ch_conn: Any = self._clickhouse_pool.get_connection()

        Logger.info(Messages.MONTHLY_STATISTICS_CLICKHOUSE_QUERY)
        query_start: float = time.time()
        ch_table: str = load_config("database")["clickhouse"]["table"]

        # 使用 ClickHouse 的日期函数
        query = Scripts.MONTHLY_PUBLISH_COUNT_CLICKHOUSE_QUERY(ch_table)

        try:
            results: Any = await asyncio.to_thread(ch_conn.execute, query)
            query_time: float = time.time() - query_start

            # 安全转换为字典列表
            result: List[Dict[str, Any]] = []
            for r in results:
                try:
                    result.append(
                        {
                            "year_month": str(r[0]) if r[0] is not None else "",
                            "count": int(r[1]) if r[1] is not None else 0,
                        }
                    )
                except (ValueError, TypeError) as e:
                    Logger.debug(Messages.CLICKHOUSE_QUERY_ROW_CONVERSION_FAILED(e))
                    continue

            total_time: float = time.time() - start
            Logger.info(
                Messages.CLICKHOUSE_MONTHLY_QUERY_RESULT(
                    query_time, total_time, len(result)
                )
            )

            return result
        except AttributeError as ae:
            Logger.error(Messages.CLICKHOUSE_ATTR_ERROR(ae))
            Logger.error(Messages.CLICKHOUSE_DETAIL_ERROR(traceback.format_exc()))
            raise
        except Exception as e:
            Logger.error(Messages.CLICKHOUSE_DEGRADE_TO_DB(type(e).__name__, e))
            Logger.debug(Messages.CLICKHOUSE_DETAIL_EXCEPTION(traceback.format_exc()))
            raise
        finally:
            if ch_conn:
                self._clickhouse_pool.return_connection(ch_conn)


@lru_cache()
def get_article_mapper() -> ArticleMapper:
    """获取 ArticleMapper 单例实例"""
    return ArticleMapper()
