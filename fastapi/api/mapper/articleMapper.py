from functools import lru_cache
from sqlmodel import Session, select
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import os
import time
from config import load_config, get_hive_connection_pool, HiveConnectionPool
from entity.po import Article
from common.utils import fileLogger as logger

class ArticleMapper:

    def __init__(self):
        self._hive_pool: HiveConnectionPool = get_hive_connection_pool()

    def get_top10_articles_hive_mapper(self):
        """获取前10篇文章 - Hive 查表（无缓存,由 service 层负责缓存）"""
        
        columns = [
            "id", "title", "tags", "status", "views", "create_at", "update_at", 
            "content", "user_id", "sub_category_id", "username"
        ]
        
        start = time.time()
        hive_conn = None
        try:
            # 从连接池获取连接
            pool_start = time.time()
            hive_conn = self._hive_pool.get_connection()
            pool_time = time.time() - pool_start
            
            # 查询 Hive
            logger.info("get_top10_articles_hive_mapper: 从 Hive 查询")
            query_start = time.time()
            with hive_conn.cursor() as cursor:
                cursor.execute(f"SELECT {', '.join(columns)} FROM articles ORDER BY views DESC LIMIT 10")
                top10 = cursor.fetchall()
            
            query_time = time.time() - query_start
            
            # 转换为字典
            result = [dict(zip(columns, r)) for r in top10]
            
            total_time = time.time() - start
            logger.info(f"get_top10_articles_hive_mapper: 获取连接耗时 {pool_time:.3f}s, 查询耗时 {query_time:.3f}s, 总耗时 {total_time:.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"get_top10_articles_hive_mapper 失败: {e}")
            raise
        finally:
            # 归还连接到池
            if hive_conn:
                self._hive_pool.return_connection(hive_conn)
    
    def get_hive_connection(self):
        """获取 Hive 连接（用于缓存版本检查）"""
        return self._hive_pool.get_connection()
    
    def return_hive_connection(self, conn):
        """归还 Hive 连接"""
        self._hive_pool.return_connection(conn)

    def get_top10_articles_spark_mapper(self):
        FILE_PATH: str = load_config("files")["excel_path"]
        csv_file = os.path.normpath(os.path.join(os.getcwd(), FILE_PATH, "articles.csv"))
        csv_file = os.path.abspath(csv_file)
        columns = [
            "id", "title", "tags", "status", "views", "create_at", "update_at", "content", "user_id", "sub_category_id", "username"
        ]
        try:
            spark = SparkSession.builder.appName("ArticleTop10").getOrCreate()
            df = spark.read.option("header", True).csv(csv_file)
            df = df.withColumn("views", col("views").cast("int"))
            for c in ["id", "status", "user_id", "sub_category_id"]:
                df = df.withColumn(c, col(c).cast("int"))
            for c in ["create_at", "update_at"]:
                df = df.withColumn(c, col(c).cast("string"))
            # username 字段直接从 csv 读取
            top10_rows = df.orderBy(col("views").desc()).limit(10).collect()
            return [{k: r[k] for k in columns if k in r.asDict()} for r in top10_rows]
        except Exception as e:
            logger.error(f"Spark 查询失败: {e}")
            raise e

    def get_top10_articles_db_mapper(self, db: Session):
        statement = select(Article).order_by(Article.views.desc()).limit(10)
        return db.exec(statement).all()

    def get_all_articles_mapper(self, db: Session) -> list[Article]:
        statement = select(Article)
        return db.exec(statement).all()
    
    def get_article_by_id_mapper(self, article_id: int, db: Session) -> Article | None:
        statement = select(Article).where(Article.id == article_id)
        return db.exec(statement).first()

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

    def get_category_article_count_hive_mapper(self) -> list[dict]:
        """
        从Hive获取按父分类排序的文章数量
        """
        start = time.time()
        hive_conn = None
        try:
            hive_conn = self._hive_pool.get_connection()
            
            logger.info("get_category_article_count_hive_mapper: 从 Hive 查询")
            query_start = time.time()
            with hive_conn.cursor() as cursor:
                # 查询文章按sub_category_id分组统计
                cursor.execute("""
                    SELECT sub_category_id, COUNT(*) as count
                    FROM articles
                    WHERE status = 1
                    GROUP BY sub_category_id
                    ORDER BY count DESC
                """)
                results = cursor.fetchall()
            
            query_time = time.time() - query_start
            
            # 转换为字典列表
            result = [{"sub_category_id": int(r[0]), "count": int(r[1])} for r in results]
            
            total_time = time.time() - start
            logger.info(f"get_category_article_count_hive_mapper: 查询耗时 {query_time:.3f}s, 总耗时 {total_time:.3f}s, 获取 {len(result)} 个分类")
            
            return result
        except Exception as e:
            logger.error(f"get_category_article_count_hive_mapper 失败: {e}")
            raise
        finally:
            if hive_conn:
                self._hive_pool.return_connection(hive_conn)

    def get_category_article_count_spark_mapper(self) -> list[dict]:
        """
        从Spark获取按父分类排序的文章数量
        """
        FILE_PATH: str = load_config("files")["excel_path"]
        csv_file = os.path.normpath(os.path.join(os.getcwd(), FILE_PATH, "articles.csv"))
        csv_file = os.path.abspath(csv_file)
        
        try:
            spark = SparkSession.builder.appName("CategoryCount").getOrCreate()
            df = spark.read.option("header", True).csv(csv_file)
            df = df.withColumn("sub_category_id", col("sub_category_id").cast("int"))
            df = df.withColumn("status", col("status").cast("int"))
            
            # 过滤status=1的文章，按sub_category_id分组统计
            df_grouped = df.filter(col("status") == 1).groupBy("sub_category_id").count()
            df_sorted = df_grouped.orderBy(col("count").desc())
            
            results = df_sorted.collect()
            return [{"sub_category_id": int(r["sub_category_id"]), "count": int(r["count"])} for r in results]
        except Exception as e:
            logger.error(f"Spark 查询失败: {e}")
            raise

    def get_category_article_count_db_mapper(self, db: Session) -> list[dict]:
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

    def get_monthly_publish_count_hive_mapper(self) -> list[dict]:
        """
        从Hive获取最近24个月的文章发布数量统计（包含零值月份）
        说明: 返回的是过去24个月内有数据的月份，缺失月份由service层补零
        """
        start = time.time()
        hive_conn = None
        try:
            hive_conn = self._hive_pool.get_connection()
            
            logger.info("get_monthly_publish_count_hive_mapper: 从 Hive 查询")
            query_start = time.time()
            with hive_conn.cursor() as cursor:
                # 按月统计最近24个月的文章数，使用Hive的substr和concat处理日期
                cursor.execute("""
                    SELECT substr(create_at, 1, 7) as year_month, COUNT(*) as count
                    FROM articles
                    WHERE status = 1
                    AND create_at >= date_sub(current_date(), 730)
                    GROUP BY substr(create_at, 1, 7)
                    ORDER BY year_month DESC
                """)
                results = cursor.fetchall()
            
            query_time = time.time() - query_start
            
            # 转换为字典列表
            result = [{"year_month": str(r[0]), "count": int(r[1])} for r in results]
            
            total_time = time.time() - start
            logger.info(f"get_monthly_publish_count_hive_mapper: 查询耗时 {query_time:.3f}s, 总耗时 {total_time:.3f}s, 获取过去24个月中 {len(result)} 个有数据的月份")
            
            return result
        except Exception as e:
            logger.error(f"get_monthly_publish_count_hive_mapper 失败: {e}")
            raise
        finally:
            if hive_conn:
                self._hive_pool.return_connection(hive_conn)

    def get_monthly_publish_count_spark_mapper(self) -> list[dict]:
        """
        从Spark获取最近24个月的文章发布数量统计（包含零值月份）
        说明: 返回的是过去24个月内有数据的月份，缺失月份由service层补零
        """
        from pyspark.sql.functions import trunc, date_sub, current_date, date_format
        
        FILE_PATH: str = load_config("files")["excel_path"]
        csv_file = os.path.normpath(os.path.join(os.getcwd(), FILE_PATH, "articles.csv"))
        csv_file = os.path.abspath(csv_file)
        
        try:
            spark = SparkSession.builder.appName("MonthlyPublish").getOrCreate()
            df = spark.read.option("header", True).csv(csv_file)
            df = df.withColumn("create_at", col("create_at").cast("timestamp"))
            df = df.withColumn("status", col("status").cast("int"))
            
            # 过滤最近24个月的数据
            ten_months_ago = date_sub(current_date(), 730)  # 近24个月
            df_filtered = df.filter((col("status") == 1) & (col("create_at") >= ten_months_ago))
            
            # 按月分组统计，不限制结果让service层补零
            df_grouped = df_filtered.withColumn("year_month", date_format(col("create_at"), "yyyy-MM")).groupBy("year_month").count()
            df_sorted = df_grouped.orderBy(col("year_month").desc())
            
            results = df_sorted.collect()
            return [{"year_month": r["year_month"], "count": int(r["count"])} for r in results]
        except Exception as e:
            logger.error(f"Spark 查询失败: {e}")
            raise

    def get_monthly_publish_count_db_mapper(self, db: Session) -> list[dict]:
        """
        从DB获取最近24个月的文章发布数量统计（包含零值月份）
        说明: 返回的是过去24个月内有数据的月份，缺失月份由service层补零
        """
        from datetime import datetime, timedelta
        
        statement = select(Article).where(Article.status == 1)
        articles = db.exec(statement).all()
        
        # 过滤最近24个月的文章
        ten_months_ago = datetime.now() - timedelta(days=730)
        filtered_articles = [a for a in articles if a.create_at and a.create_at >= ten_months_ago]
        
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