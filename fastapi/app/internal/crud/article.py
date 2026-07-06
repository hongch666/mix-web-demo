import time
import traceback
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.core.base import Constants, Logger
from app.core.config import load_config
from app.core.db import ClickhouseConnectionPool, engine, get_clickhouse_connection_pool
from app.internal.models import (
    Article,
    Category,
    Collect,
    Focus,
    Like,
    SubCategory,
    User,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session as SyncSession


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
                        Logger.debug(f"值转换失败 {col}={val}: {val_e}")
                        row_dict[col] = None
                result.append(row_dict)
            except Exception as row_e:
                Logger.debug(f"行数据转换失败: {row_e}")
                continue
        return result

    async def _get_top10_articles_clickhouse_mapper_sync(
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
        Logger.info(Constants.TOP10_CLICKHOUSE_QUERY)
        query_start: float = time.time()
        ch_table: str = load_config("database")["clickhouse"]["table"]
        query = (
            f"SELECT {', '.join(columns)} FROM {ch_table} ORDER BY views DESC LIMIT 10"
        )

        try:
            results: List[tuple] = ch_conn.execute(query)
            query_time: float = time.time() - query_start

            # 安全转换为字典
            result: List[Dict[str, Any]] = self._safe_convert_to_list_of_dicts(
                results, columns
            )

            total_time: float = time.time() - start
            Logger.info(
                f"获取连接耗时 {pool_time:.3f}s, 查询耗时 {query_time:.3f}s, 总耗时 {total_time:.3f}s"
            )

            return result
        except AttributeError as ae:
            Logger.error(f"ClickHouse 查询失败，属性错误: {ae}")
            Logger.error(f"详细错误: {traceback.format_exc()}")
            # 降级到 DB
            return await self._get_top10_articles_db_mapper_sync(SyncSession(engine))
        except Exception as e:
            Logger.error(f"ClickHouse 查询失败，降级为 DB: {type(e).__name__}: {e}")
            Logger.debug(f"详细异常: {traceback.format_exc()}")
            # 降级到 DB
            return await self._get_top10_articles_db_mapper_sync(SyncSession(engine))
        finally:
            # 归还连接到池
            if ch_conn:
                self._clickhouse_pool.return_connection(ch_conn)

    async def _get_top10_articles_hive_mapper_sync(self) -> List[Dict[str, Any]]:
        """获取前10篇文章 - Hive 查表（已弃用，保留向后兼容）"""
        Logger.warning("Hive 已删除，使用 DB 替代")
        return await self._get_top10_articles_db_mapper_sync(SyncSession(engine))

    async def _get_top10_articles_spark_mapper_sync(self) -> List[Dict[str, Any]]:
        """获取前10篇文章 - Spark 查表（已弃用，保留向后兼容）"""
        Logger.warning("Spark 已删除，使用 DB 替代")
        return await self._get_top10_articles_db_mapper_sync(SyncSession(engine))

    async def _get_top10_articles_db_mapper_sync(self, db: AsyncSession) -> List[Article]:
        statement = select(Article).order_by(Article.views.desc()).limit(10)
        return (await db.execute(statement)).scalars().all()

    async def _get_clickhouse_connection_sync(self) -> Any:
        """获取 ClickHouse 连接（用于缓存版本检查）"""
        return self._clickhouse_pool.get_connection()

    async def _return_clickhouse_connection_sync(self, conn: Any) -> None:
        """归还 ClickHouse 连接"""
        self._clickhouse_pool.return_connection(conn)

    async def _get_all_articles_mapper_sync(self, db: AsyncSession) -> List[Article]:
        statement = select(Article)
        return (await db.execute(statement)).scalars().all()

    async def _iter_all_articles_mapper_sync(
        self, db: AsyncSession, batch_size: int = 500
    ) -> AsyncGenerator[List[Article], None]:
        """按批获取文章，避免一次性加载整表"""
        if batch_size <= 0:
            batch_size = 500

        last_id: int = 0
        while True:
            statement = (
                select(Article)
                .where(Article.id > last_id)
                .order_by(Article.id.asc())
                .limit(batch_size)
            )
            articles = (await db.execute(statement)).scalars().all()
            if not articles:
                break

            yield articles
            last_id = articles[-1].id

    async def _get_articles_for_excel_export_mapper_sync(
        self, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """获取导出Excel所需文章数据（连表聚合）"""
        result: List[Dict[str, Any]] = []
        async for batch in self._iter_articles_for_excel_export_mapper_sync(db):
            result.extend(batch)
        return result

    async def _iter_articles_for_excel_export_mapper_sync(
        self, db: AsyncSession, batch_size: int = 200
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """分批获取导出Excel所需文章数据，避免大结果集一次性堆积在内存中

        优化策略：先查询文章基础信息（仅LEFT JOIN分类/用户小表），
        再单独查询点赞/收藏/关注数，避免整表 GROUP BY 子查询。
        """
        if batch_size <= 0:
            batch_size = 200

        last_id = 0
        while True:
            # 第1步：查询文章基础信息（只做简单的 FK 关联）
            base_statement = (
                select(
                    Article.id.label("id"),
                    Article.title.label("title"),
                    Article.content.label("content"),
                    Article.user_id.label("user_id"),
                    User.name.label("username"),
                    Article.tags.label("tags"),
                    Article.status.label("status"),
                    Article.create_at.label("create_at"),
                    Article.update_at.label("update_at"),
                    Article.views.label("views"),
                    SubCategory.name.label("sub_category_name"),
                    Category.name.label("category_name"),
                )
                .select_from(Article)
                .outerjoin(User, User.id == Article.user_id)
                .outerjoin(SubCategory, SubCategory.id == Article.sub_category_id)
                .outerjoin(Category, Category.id == SubCategory.category_id)
                .where(Article.id > last_id)
                .order_by(Article.id.asc())
                .limit(batch_size)
            )
            base_rows = (await db.execute(base_statement)).all()
            if not base_rows:
                break

            # 收集当前批次的文章ID和用户ID
            article_ids: List[int] = [row.id for row in base_rows]
            user_ids: List[int] = [row.user_id for row in base_rows if row.user_id is not None]

            # 第2步：批量查询点赞数
            like_statement = (
                select(
                    Like.article_id.label("article_id"),
                    func.count(Like.id).label("like_count"),
                )
                .where(Like.article_id.in_(article_ids))
                .group_by(Like.article_id)
            )
            like_rows = (await db.execute(like_statement)).all()
            like_map: Dict[int, int] = {row.article_id: row.like_count for row in like_rows}

            # 第3步：批量查询收藏数
            collect_statement = (
                select(
                    Collect.article_id.label("article_id"),
                    func.count(Collect.id).label("collect_count"),
                )
                .where(Collect.article_id.in_(article_ids))
                .group_by(Collect.article_id)
            )
            collect_rows = (await db.execute(collect_statement)).all()
            collect_map: Dict[int, int] = {row.article_id: row.collect_count for row in collect_rows}

            # 第4步：批量查询作者关注数（按作者分别统计）
            follow_map: Dict[int, int] = {}
            if user_ids:
                # 去重 user_ids 减少查询范围
                unique_user_ids: List[int] = list(set(user_ids))
                follow_statement = (
                    select(
                        Focus.focus_id.label("author_id"),
                        func.count(Focus.id).label("author_follow_count"),
                    )
                    .where(Focus.focus_id.in_(unique_user_ids))
                    .group_by(Focus.focus_id)
                )
                follow_rows = (await db.execute(follow_statement)).all()
                follow_map = {row.author_id: row.author_follow_count for row in follow_rows}

            result: List[Dict[str, Any]] = []
            for row in base_rows:
                result.append(
                    {
                        "id": row.id,
                        "title": row.title,
                        "content": row.content,
                        "username": row.username,
                        "tags": row.tags,
                        "status": row.status,
                        "create_at": row.create_at,
                        "update_at": row.update_at,
                        "views": row.views,
                        "sub_category_name": row.sub_category_name,
                        "category_name": row.category_name,
                        "like_count": like_map.get(row.id, 0),
                        "collect_count": collect_map.get(row.id, 0),
                        "author_follow_count": follow_map.get(row.user_id, 0) if row.user_id else 0,
                    }
                )

            yield result
            last_id = base_rows[-1].id

    async def _get_article_by_id_mapper_sync(
        self, article_id: int, db: AsyncSession
    ) -> Optional[Article]:
        statement = select(Article).where(Article.id == article_id)
        return (await db.execute(statement)).scalars().first()

    async def _get_articles_by_ids_mapper_sync(
        self, article_ids: List[int], db: AsyncSession
    ) -> Dict[int, Article]:
        """批量获取文章信息，返回 {article_id: Article} 字典"""
        if not article_ids:
            return {}
        statement = select(Article).where(Article.id.in_(article_ids))
        articles = (await db.execute(statement)).scalars().all()
        return {article.id: article for article in articles}

    async def _get_total_views_mapper_sync(self, db: AsyncSession) -> int:
        """获取所有文章的总阅读量"""
        statement = select(func.coalesce(func.sum(Article.views), 0))
        return (await db.execute(statement)).scalar_one()

    async def _get_total_articles_mapper_sync(self, db: AsyncSession) -> int:
        """获取文章总数"""
        statement = select(func.count(Article.id))
        return (await db.execute(statement)).scalar_one()

    async def _get_active_authors_mapper_sync(self, db: AsyncSession) -> int:
        """获取活跃作者数（所有有文章的用户）"""
        statement = select(func.count(func.distinct(Article.user_id)))
        return (await db.execute(statement)).scalar_one()

    async def _get_average_views_mapper_sync(self, db: AsyncSession) -> float:
        """获取平均阅读次数"""
        statement = select(func.coalesce(func.avg(Article.views), 0))
        average_views: float = (await db.execute(statement)).scalar_one()
        return round(float(average_views), 2)

    async def _get_category_article_count_clickhouse_mapper_sync(
        self,
    ) -> List[Dict[str, Any]]:
        """
        从ClickHouse获取按父分类排序的文章数量
        """
        start: float = time.time()
        ch_conn: Any = self._clickhouse_pool.get_connection()

        Logger.info(Constants.CATEGORY_STATISTICS_CLICKHOUSE_QUERY)
        query_start: float = time.time()
        ch_table: str = load_config("database")["clickhouse"]["table"]
        query = f"SELECT sub_category_id, count() as count FROM {ch_table} WHERE status = 1 GROUP BY sub_category_id ORDER BY count DESC"

        try:
            results: Any = ch_conn.execute(query)
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
                    Logger.debug(f"行转换失败: {e}，跳过此行")
                    continue

            total_time: float = time.time() - start
            Logger.info(
                f"查询耗时 {query_time:.3f}s, 总耗时 {total_time:.3f}s, 获取 {len(result)} 个分类"
            )

            return result
        except AttributeError as ae:
            Logger.error(f"ClickHouse 查询失败，属性错误: {ae}")
            Logger.error(f"详细错误: {traceback.format_exc()}")
            # 降级到 DB
            return await self._get_category_article_count_db_mapper_sync(
                SyncSession(engine)
            )
        except Exception as e:
            Logger.error(f"ClickHouse 查询失败，降级为 DB: {type(e).__name__}: {e}")
            Logger.debug(f"详细异常: {traceback.format_exc()}")
            # 降级到 DB
            return await self._get_category_article_count_db_mapper_sync(
                SyncSession(engine)
            )
        finally:
            if ch_conn:
                self._clickhouse_pool.return_connection(ch_conn)

    async def _get_category_article_count_hive_mapper_sync(
        self,
    ) -> List[Dict[str, Any]]:
        """
        从Hive获取按父分类排序的文章数量（已弃用）
        """
        Logger.warning("Hive 已删除，使用 DB 替代")
        return await self._get_category_article_count_db_mapper_sync(SyncSession(engine))

    async def _get_category_article_count_spark_mapper_sync(
        self,
    ) -> List[Dict[str, Any]]:
        """
        从Spark获取按父分类排序的文章数量（已弃用）
        """
        Logger.warning("Spark 已删除，使用 DB 替代")
        return await self._get_category_article_count_db_mapper_sync(SyncSession(engine))

    async def _get_category_article_count_db_mapper_sync(
        self, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        从DB获取按父分类排序的文章数量
        """
        count_expr: Any = func.count(Article.id)
        statement = (
            select(
                Article.sub_category_id.label("sub_category_id"),
                count_expr.label("count"),
            )
            .where(Article.status == 1)
            .group_by(Article.sub_category_id)
            .order_by(count_expr.desc())
        )
        rows = (await db.execute(statement)).all()

        return [
            {
                "sub_category_id": row._mapping["sub_category_id"],
                "count": (
                    int(row._mapping["count"])
                    if row._mapping["count"] is not None
                    else 0
                ),
            }
            for row in rows
        ]

    async def _get_monthly_publish_count_clickhouse_mapper_sync(
        self,
    ) -> List[Dict[str, Any]]:
        """
        从ClickHouse获取最近24个月的文章发布数量统计（包含零值月份）
        说明: 返回的是过去24个月内有数据的月份，缺失月份由service层补零
        """
        start: float = time.time()
        ch_conn: Any = self._clickhouse_pool.get_connection()

        Logger.info(Constants.MONTHLY_STATISTICS_CLICKHOUSE_QUERY)
        query_start: float = time.time()
        ch_table: str = load_config("database")["clickhouse"]["table"]

        # 使用 ClickHouse 的日期函数
        query = f"""
            SELECT
                formatDateTime(create_at, '%Y-%m') as year_month,
                count() as count
            FROM {ch_table}
            WHERE status = 1 AND create_at >= subtractMonths(now(), 24)
            GROUP BY year_month
            ORDER BY year_month DESC
        """

        try:
            results: Any = ch_conn.execute(query)
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
                    Logger.debug(f"行转换失败: {e}，跳过此行")
                    continue

            total_time: float = time.time() - start
            Logger.info(
                f"查询耗时 {query_time:.3f}s, 总耗时 {total_time:.3f}s, 获取过去24个月中 {len(result)} 个有数据的月份"
            )

            return result
        except AttributeError as ae:
            Logger.error(f"ClickHouse 查询失败，属性错误: {ae}")
            Logger.error(f"详细错误: {traceback.format_exc()}")
            # 降级到 DB
            return await self._get_monthly_publish_count_db_mapper_sync(SyncSession(engine))
        except Exception as e:
            Logger.error(f"ClickHouse 查询失败，降级为 DB: {type(e).__name__}: {e}")
            Logger.debug(f"详细异常: {traceback.format_exc()}")
            # 降级到 DB
            return await self._get_monthly_publish_count_db_mapper_sync(SyncSession(engine))
        finally:
            if ch_conn:
                self._clickhouse_pool.return_connection(ch_conn)

    async def _get_monthly_publish_count_hive_mapper_sync(self) -> List[Dict[str, Any]]:
        """
        从Hive获取最近24个月的文章发布数量统计（已弃用）
        """
        Logger.warning("Hive 已删除，使用 DB 替代")
        return await self._get_monthly_publish_count_db_mapper_sync(SyncSession(engine))

    async def _get_monthly_publish_count_spark_mapper_sync(
        self,
    ) -> List[Dict[str, Any]]:
        """
        从Spark获取最近24个月的文章发布数量统计（已弃用）
        """
        Logger.warning("Spark 已删除，使用 DB 替代")
        return await self._get_monthly_publish_count_db_mapper_sync(SyncSession(engine))

    async def _get_monthly_publish_count_db_mapper_sync(
        self, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        从DB获取最近24个月的文章发布数量统计（包含零值月份）
        说明: 返回的是过去24个月内有数据的月份，缺失月份由service层补零
        """

        months_ago: datetime = datetime.now() - timedelta(days=730)
        year_month: Any = func.date_format(Article.create_at, "%Y-%m")
        count_expr: Any = func.count(Article.id)
        statement = (
            select(
                year_month.label("year_month"),
                count_expr.label("count"),
            )
            .where(
                Article.status == 1,
                Article.create_at >= months_ago,
            )
            .group_by(year_month)
            .order_by(year_month.desc())
        )
        rows = (await db.execute(statement)).all()

        return [
            {
                "year_month": row._mapping["year_month"],
                "count": (
                    int(row._mapping["count"])
                    if row._mapping["count"] is not None
                    else 0
                ),
            }
            for row in rows
        ]

    async def get_clickhouse_connection_async(self) -> Any:
        return await self._get_clickhouse_connection_sync()

    async def return_clickhouse_connection_async(self, conn: Any) -> None:
        await self._return_clickhouse_connection_sync(conn)

    async def get_top10_articles_clickhouse_mapper_async(
        self,
    ) -> List[Dict[str, Any]]:
        return await self._get_top10_articles_clickhouse_mapper_sync()

    async def get_top10_articles_hive_mapper_async(self) -> List[Dict[str, Any]]:
        return await self._get_top10_articles_hive_mapper_sync()

    async def get_top10_articles_spark_mapper_async(self) -> List[Dict[str, Any]]:
        return await self._get_top10_articles_spark_mapper_sync()

    async def get_top10_articles_db_mapper_async(self, db: AsyncSession) -> List[Article]:
        return await self._get_top10_articles_db_mapper_sync(db)

    async def get_all_articles_mapper_async(self, db: AsyncSession) -> List[Article]:
        return await self._get_all_articles_mapper_sync(db)

    async def get_articles_for_excel_export_mapper_async(
        self, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        return await self._get_articles_for_excel_export_mapper_sync(db)

    async def get_article_by_id_mapper_async(
        self, article_id: int, db: AsyncSession
    ) -> Optional[Article]:
        return await self._get_article_by_id_mapper_sync(article_id, db)

    async def get_articles_by_ids_mapper_async(
        self, article_ids: List[int], db: AsyncSession
    ) -> Dict[int, Article]:
        return await self._get_articles_by_ids_mapper_sync(article_ids, db)

    async def get_total_views_mapper_async(self, db: AsyncSession) -> int:
        return await self._get_total_views_mapper_sync(db)

    async def get_total_articles_mapper_async(self, db: AsyncSession) -> int:
        return await self._get_total_articles_mapper_sync(db)

    async def get_active_authors_mapper_async(self, db: AsyncSession) -> int:
        return await self._get_active_authors_mapper_sync(db)

    async def get_average_views_mapper_async(self, db: AsyncSession) -> float:
        return await self._get_average_views_mapper_sync(db)

    async def get_category_article_count_clickhouse_mapper_async(
        self,
    ) -> List[Dict[str, Any]]:
        return await self._get_category_article_count_clickhouse_mapper_sync()

    async def get_category_article_count_hive_mapper_async(
        self,
    ) -> List[Dict[str, Any]]:
        return await self._get_category_article_count_hive_mapper_sync()

    async def get_category_article_count_spark_mapper_async(
        self,
    ) -> List[Dict[str, Any]]:
        return await self._get_category_article_count_spark_mapper_sync()

    async def get_category_article_count_db_mapper_async(
        self, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        return await self._get_category_article_count_db_mapper_sync(db)

    async def get_monthly_publish_count_clickhouse_mapper_async(
        self,
    ) -> List[Dict[str, Any]]:
        return await self._get_monthly_publish_count_clickhouse_mapper_sync()

    async def get_monthly_publish_count_hive_mapper_async(
        self,
    ) -> List[Dict[str, Any]]:
        return await self._get_monthly_publish_count_hive_mapper_sync()

    async def get_monthly_publish_count_spark_mapper_async(
        self,
    ) -> List[Dict[str, Any]]:
        return await self._get_monthly_publish_count_spark_mapper_sync()

    async def get_monthly_publish_count_db_mapper_async(
        self, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        return await self._get_monthly_publish_count_db_mapper_sync(db)


@lru_cache()
def get_article_mapper() -> ArticleMapper:
    """获取 ArticleMapper 单例实例"""
    return ArticleMapper()
