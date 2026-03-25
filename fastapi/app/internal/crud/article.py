import time
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional

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
from sqlalchemy.orm import Session


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

    def get_top10_articles_clickhouse_mapper(self) -> List[Dict[str, Any]]:
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
        ch_table = load_config("database")["clickhouse"]["table"]
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
            import traceback

            Logger.error(f"详细错误: {traceback.format_exc()}")
            # 降级到 DB
            return self.get_top10_articles_db_mapper(Session(engine))
        except Exception as e:
            Logger.error(f"ClickHouse 查询失败，降级为 DB: {type(e).__name__}: {e}")
            import traceback

            Logger.debug(f"详细异常: {traceback.format_exc()}")
            # 降级到 DB
            return self.get_top10_articles_db_mapper(Session(engine))
        finally:
            # 归还连接到池
            if ch_conn:
                self._clickhouse_pool.return_connection(ch_conn)

    def get_top10_articles_hive_mapper(self) -> List[Dict[str, Any]]:
        """获取前10篇文章 - Hive 查表（已弃用，保留向后兼容）"""
        Logger.warning("Hive 已删除，使用 DB 替代")
        return self.get_top10_articles_db_mapper(Session(engine))

    def get_top10_articles_spark_mapper(self) -> List[Dict[str, Any]]:
        """获取前10篇文章 - Spark 查表（已弃用，保留向后兼容）"""
        Logger.warning("Spark 已删除，使用 DB 替代")
        return self.get_top10_articles_db_mapper(Session(engine))

    def get_top10_articles_db_mapper(self, db: Session) -> List[Article]:
        statement = select(Article).order_by(Article.views.desc()).limit(10)
        return db.exec(statement).all()

    def get_clickhouse_connection(self) -> Any:
        """获取 ClickHouse 连接（用于缓存版本检查）"""
        return self._clickhouse_pool.get_connection()

    def return_clickhouse_connection(self, conn: Any) -> None:
        """归还 ClickHouse 连接"""
        self._clickhouse_pool.return_connection(conn)

    def get_all_articles_mapper(self, db: Session) -> List[Article]:
        statement = select(Article)
        return db.exec(statement).all()

    def get_articles_for_excel_export_mapper(self, db: Session) -> List[Dict[str, Any]]:
        """获取导出Excel所需文章数据（连表聚合）"""

        like_count_subquery = (
            select(
                Like.article_id.label("article_id"),
                func.count(Like.id).label("like_count"),
            )
            .group_by(Like.article_id)
            .subquery()
        )
        collect_count_subquery = (
            select(
                Collect.article_id.label("article_id"),
                func.count(Collect.id).label("collect_count"),
            )
            .group_by(Collect.article_id)
            .subquery()
        )
        follow_count_subquery = (
            select(
                Focus.focus_id.label("author_id"),
                func.count(Focus.id).label("author_follow_count"),
            )
            .group_by(Focus.focus_id)
            .subquery()
        )

        statement = (
            select(
                Article.id.label("id"),
                Article.title.label("title"),
                Article.content.label("content"),
                User.name.label("username"),
                Article.tags.label("tags"),
                Article.status.label("status"),
                Article.create_at.label("create_at"),
                Article.update_at.label("update_at"),
                Article.views.label("views"),
                SubCategory.name.label("sub_category_name"),
                Category.name.label("category_name"),
                func.coalesce(like_count_subquery.c.like_count, 0).label("like_count"),
                func.coalesce(collect_count_subquery.c.collect_count, 0).label(
                    "collect_count"
                ),
                func.coalesce(follow_count_subquery.c.author_follow_count, 0).label(
                    "author_follow_count"
                ),
            )
            .select_from(Article)
            .outerjoin(User, User.id == Article.user_id)
            .outerjoin(SubCategory, SubCategory.id == Article.sub_category_id)
            .outerjoin(Category, Category.id == SubCategory.category_id)
            .outerjoin(
                like_count_subquery, like_count_subquery.c.article_id == Article.id
            )
            .outerjoin(
                collect_count_subquery,
                collect_count_subquery.c.article_id == Article.id,
            )
            .outerjoin(
                follow_count_subquery,
                follow_count_subquery.c.author_id == Article.user_id,
            )
            .order_by(Article.id.asc())
        )
        rows = db.exec(statement).all()

        result: List[Dict[str, Any]] = []
        for row in rows:
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
                    "like_count": row.like_count,
                    "collect_count": row.collect_count,
                    "author_follow_count": row.author_follow_count,
                }
            )

        return result

    def get_article_by_id_mapper(
        self, article_id: int, db: Session
    ) -> Optional[Article]:
        statement = select(Article).where(Article.id == article_id)
        return db.exec(statement).first()

    def get_articles_by_ids_mapper(
        self, article_ids: List[int], db: Session
    ) -> Dict[int, Article]:
        """批量获取文章信息，返回 {article_id: Article} 字典"""
        if not article_ids:
            return {}
        statement = select(Article).where(Article.id.in_(article_ids))
        articles = db.exec(statement).all()
        return {article.id: article for article in articles}

    def get_total_views_mapper(self, db: Session) -> int:
        """获取所有文章的总阅读量"""
        statement = select(Article)
        articles = db.exec(statement).all()
        return sum(article.views for article in articles)

    def get_total_articles_mapper(self, db: Session) -> int:
        """获取文章总数"""
        statement = select(Article)
        articles = db.exec(statement).all()
        return len(articles)

    def get_active_authors_mapper(self, db: Session) -> int:
        """获取活跃作者数（所有有文章的用户）"""
        statement = select(Article)
        articles = db.exec(statement).all()
        active_author_ids = set(article.user_id for article in articles)
        return len(active_author_ids)

    def get_average_views_mapper(self, db: Session) -> float:
        """获取平均阅读次数"""
        statement = select(Article)
        articles = db.exec(statement).all()
        if not articles:
            return 0
        total_views = sum(article.views for article in articles)
        return round(total_views / len(articles), 2)

    def get_category_article_count_clickhouse_mapper(self) -> List[Dict[str, Any]]:
        """
        从ClickHouse获取按父分类排序的文章数量
        """
        start = time.time()
        ch_conn = self._clickhouse_pool.get_connection()

        Logger.info(Constants.CATEGORY_STATISTICS_CLICKHOUSE_QUERY)
        query_start = time.time()
        ch_table = load_config("database")["clickhouse"]["table"]
        query = f"SELECT sub_category_id, count() as count FROM {ch_table} WHERE status = 1 GROUP BY sub_category_id ORDER BY count DESC"

        try:
            results = ch_conn.execute(query)
            query_time = time.time() - query_start

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

            total_time = time.time() - start
            Logger.info(
                f"查询耗时 {query_time:.3f}s, 总耗时 {total_time:.3f}s, 获取 {len(result)} 个分类"
            )

            return result
        except AttributeError as ae:
            Logger.error(f"ClickHouse 查询失败，属性错误: {ae}")
            import traceback

            Logger.error(f"详细错误: {traceback.format_exc()}")
            # 降级到 DB
            return self.get_category_article_count_db_mapper(Session(engine))
        except Exception as e:
            Logger.error(f"ClickHouse 查询失败，降级为 DB: {type(e).__name__}: {e}")
            import traceback

            Logger.debug(f"详细异常: {traceback.format_exc()}")
            # 降级到 DB
            return self.get_category_article_count_db_mapper(Session(engine))
        finally:
            if ch_conn:
                self._clickhouse_pool.return_connection(ch_conn)

    def get_category_article_count_hive_mapper(self) -> List[Dict[str, Any]]:
        """
        从Hive获取按父分类排序的文章数量（已弃用）
        """
        Logger.warning("Hive 已删除，使用 DB 替代")
        return self.get_category_article_count_db_mapper(Session(engine))

    def get_category_article_count_spark_mapper(self) -> List[Dict[str, Any]]:
        """
        从Spark获取按父分类排序的文章数量（已弃用）
        """
        Logger.warning("Spark 已删除，使用 DB 替代")
        return self.get_category_article_count_db_mapper(Session(engine))

    def get_category_article_count_db_mapper(self, db: Session) -> List[Dict[str, Any]]:
        """
        从DB获取按父分类排序的文章数量
        """
        statement = select(Article).where(Article.status == 1)
        articles = db.exec(statement).all()

        # 按sub_category_id分组统计
        category_count = {}
        for article in articles:
            if article.sub_category_id not in category_count:
                category_count[article.sub_category_id] = 0
            category_count[article.sub_category_id] += 1

        # 排序
        result = [{"sub_category_id": k, "count": v} for k, v in category_count.items()]
        result.sort(key=lambda x: x["count"], reverse=True)

        return result

    def get_monthly_publish_count_clickhouse_mapper(self) -> List[Dict[str, Any]]:
        """
        从ClickHouse获取最近24个月的文章发布数量统计（包含零值月份）
        说明: 返回的是过去24个月内有数据的月份，缺失月份由service层补零
        """
        start = time.time()
        ch_conn = self._clickhouse_pool.get_connection()

        Logger.info(Constants.MONTHLY_STATISTICS_CLICKHOUSE_QUERY)
        query_start = time.time()
        ch_table = load_config("database")["clickhouse"]["table"]

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
            results = ch_conn.execute(query)
            query_time = time.time() - query_start

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

            total_time = time.time() - start
            Logger.info(
                f"查询耗时 {query_time:.3f}s, 总耗时 {total_time:.3f}s, 获取过去24个月中 {len(result)} 个有数据的月份"
            )

            return result
        except AttributeError as ae:
            Logger.error(f"ClickHouse 查询失败，属性错误: {ae}")
            import traceback

            Logger.error(f"详细错误: {traceback.format_exc()}")
            # 降级到 DB
            return self.get_monthly_publish_count_db_mapper(Session(engine))
        except Exception as e:
            Logger.error(f"ClickHouse 查询失败，降级为 DB: {type(e).__name__}: {e}")
            import traceback

            Logger.debug(f"详细异常: {traceback.format_exc()}")
            # 降级到 DB
            return self.get_monthly_publish_count_db_mapper(Session(engine))
        finally:
            if ch_conn:
                self._clickhouse_pool.return_connection(ch_conn)

    def get_monthly_publish_count_hive_mapper(self) -> List[Dict[str, Any]]:
        """
        从Hive获取最近24个月的文章发布数量统计（已弃用）
        """
        Logger.warning("Hive 已删除，使用 DB 替代")
        return self.get_monthly_publish_count_db_mapper(Session(engine))

    def get_monthly_publish_count_spark_mapper(self) -> List[Dict[str, Any]]:
        """
        从Spark获取最近24个月的文章发布数量统计（已弃用）
        """
        Logger.warning("Spark 已删除，使用 DB 替代")
        return self.get_monthly_publish_count_db_mapper(Session(engine))

    def get_monthly_publish_count_db_mapper(self, db: Session) -> List[Dict[str, Any]]:
        """
        从DB获取最近24个月的文章发布数量统计（包含零值月份）
        说明: 返回的是过去24个月内有数据的月份，缺失月份由service层补零
        """

        statement = select(Article).where(Article.status == 1)
        articles = db.exec(statement).all()

        # 过滤最近24个月的文章
        ten_months_ago = datetime.now() - timedelta(days=730)
        filtered_articles = [
            a for a in articles if a.create_at and a.create_at >= ten_months_ago
        ]

        # 按月分组统计
        monthly_count = {}
        for article in filtered_articles:
            year_month = article.create_at.strftime("%Y-%m")
            if year_month not in monthly_count:
                monthly_count[year_month] = 0
            monthly_count[year_month] += 1

        # 排序，不限制数量让service层补零
        result = [{"year_month": k, "count": v} for k, v in monthly_count.items()]
        result.sort(key=lambda x: x["year_month"], reverse=True)

        return result


@lru_cache()
def get_article_mapper() -> ArticleMapper:
    """获取 ArticleMapper 单例实例"""
    return ArticleMapper()
