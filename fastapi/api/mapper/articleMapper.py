from sqlmodel import Session, select
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import os
import time
from config import load_config
from entity.po import Article
from common.utils import fileLogger as logger
from common.cache import get_hive_connection_pool

class ArticleMapper:

    def __init__(self):
        self._hive_pool = get_hive_connection_pool()

    def get_top10_articles_hive_mapper(self):
        """获取前10篇文章 - Hive 查表（无缓存,由 service 层负责缓存）"""
        
        columns = [
            "id", "title", "tags", "status", "views", "create_at", "update_at", 
            "content", "user_id", "sub_category_id", "username"
        ]
        
        start = time.time()
        hive_conn = None
        try:
            # ✓ 从连接池获取连接
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
            
            # ✓ 转换为字典
            result = [dict(zip(columns, r)) for r in top10]
            
            total_time = time.time() - start
            logger.info(f"get_top10_articles_hive_mapper: 获取连接耗时 {pool_time:.3f}s, 查询耗时 {query_time:.3f}s, 总耗时 {total_time:.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"get_top10_articles_hive_mapper 失败: {e}")
            raise
        finally:
            # ✓ 归还连接到池
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
        spark = SparkSession.builder.appName("ArticleTop10").getOrCreate()
        df = spark.read.option("header", True).csv(csv_file)
        df = df.withColumn("views", col("views").cast("int"))
        for c in ["id", "status", "user_id", "sub_category_id"]:
            df = df.withColumn(c, col(c).cast("int"))
        for c in ["create_at", "update_at"]:
            df = df.withColumn(c, col(c).cast("string"))
        # username 字段直接从 csv 读取
        top10_rows = df.orderBy(col("views").desc()).limit(10).collect()
        spark.stop()
        return [{k: r[k] for k in columns} for r in top10_rows]

    def get_top10_articles_db_mapper(self, db: Session):
        statement = select(Article).order_by(Article.views.desc()).limit(10)
        return db.exec(statement).all()

    def get_all_articles_mapper(self, db: Session) -> list[Article]:
        statement = select(Article)
        return db.exec(statement).all()

    def get_article_limit_mapper(self, db: Session) -> list[Article]:
        statement = select(Article).order_by(Article.create_at.desc()).limit(100)
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

# 单例模式 - 保持连接池和缓存在整个应用生命周期
_article_mapper_instance = None

def get_article_mapper() -> ArticleMapper:
    """获取 ArticleMapper 单例实例"""
    global _article_mapper_instance
    if _article_mapper_instance is None:
        _article_mapper_instance = ArticleMapper()
    return _article_mapper_instance