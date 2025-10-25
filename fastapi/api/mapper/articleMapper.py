from functools import lru_cache
from sqlmodel import Session, select
from pyhive import hive
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import os
import time
import hashlib
from config import load_config
from entity.po import Article
from common.utils import fileLogger as logger

class HiveConnectionPool:
    """Hive 连接池 - 复用连接，避免重复建立"""
    _instance = None
    _connections = []
    _max_connections = 5
    _conn_count = 0  # 统计创建的连接数
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_connection(self):
        """从池中获取连接"""
        if self._connections:
            logger.info(f"[连接池] 从池中获取复用连接，池内剩余: {len(self._connections) - 1}个")
            return self._connections.pop()
        
        # 如果池为空，创建新连接
        hive_host = load_config("database")["hive"]["host"]
        hive_port = load_config("database")["hive"]["port"]
        hive_db = load_config("database")["hive"]["database"]
        
        self._conn_count += 1
        logger.info(f"[连接池] 创建新 Hive 连接 (第{self._conn_count}个)")
        conn_start = time.time()
        conn = hive.Connection(host=hive_host, port=hive_port, database=hive_db)
        conn_time = time.time() - conn_start
        logger.info(f"[连接池] Hive 连接建立耗时 {conn_time:.3f}s")
        return conn
    
    def return_connection(self, conn):
        """归还连接到池"""
        if len(self._connections) < self._max_connections:
            self._connections.append(conn)
            logger.info(f"[连接池] 连接已归还到池，池内现有: {len(self._connections)}个")
        else:
            conn.close()
            logger.info(f"[连接池] 池已满，关闭连接")

class ArticleCache:
    """文章缓存管理 - 使用版本号检测自动更新"""
    def __init__(self):
        self._cache = None
        self._cache_time = 0
        self._cache_version = None
        self._cache_ttl = 300  # 5分钟TTL
    
    def get_cache_version(self, hive_conn):
        """获取 Hive articles 表的版本号（通过最新修改时间）"""
        try:
            with hive_conn.cursor() as cursor:
                # 获取表的最新修改时间作为版本
                cursor.execute("SHOW TBLPROPERTIES articles")
                props = cursor.fetchall()
                # 将所有属性拼接后做 hash，作为版本号
                version_str = str(props)
                return hashlib.md5(version_str.encode()).hexdigest()[:8]
        except Exception as e:
            logger.warning(f"获取表版本号失败: {e}，将跳过版本检测")
            return None
    
    def is_cache_valid(self, hive_conn):
        """检查缓存是否有效"""
        if not self._cache:
            return False
        
        # 检查 TTL
        if time.time() - self._cache_time > self._cache_ttl:
            logger.info("[缓存] TTL过期，需要刷新")
            return False
        
        # 检查版本号是否变化
        try:
            current_version = self.get_cache_version(hive_conn)
            if current_version and current_version != self._cache_version:
                logger.info(f"[缓存] 表版本已变化 (旧: {self._cache_version} → 新: {current_version})，需要刷新")
                return False
        except Exception as e:
            logger.warning(f"版本检测异常: {e}，继续使用缓存")
        
        return True
    
    def set_cache(self, data, hive_conn):
        """缓存数据并记录版本号"""
        self._cache = data
        self._cache_time = time.time()
        try:
            self._cache_version = self.get_cache_version(hive_conn)
            logger.info(f"[缓存] 更新缓存，版本号: {self._cache_version}")
        except Exception as e:
            logger.warning(f"设置缓存版本号失败: {e}")
    
    def get_cache(self):
        """获取缓存"""
        if self._cache:
            cache_age = time.time() - self._cache_time
            logger.info(f"[缓存] 返回缓存数据，缓存年龄: {cache_age:.1f}s")
        return self._cache

class ArticleMapper:

    def __init__(self):
        self._hive_pool = HiveConnectionPool()
        self._article_cache = ArticleCache()

    def get_top10_articles_hive_mapper(self):
        """获取前10篇文章 - Hive 直接查表 + 智能缓存"""
        
        columns = [
            "id", "title", "tags", "status", "views", "create_at", "update_at", 
            "content", "user_id", "sub_category_id", "username"
        ]
        
        start = time.time()
        hive_conn = None
        try:
            # ✓ 从连接池获取连接（快速复用）
            pool_start = time.time()
            hive_conn = self._hive_pool.get_connection()
            pool_time = time.time() - pool_start
            
            # ✓ 检查缓存是否有效（版本号 + TTL）
            if self._article_cache.is_cache_valid(hive_conn):
                result = self._article_cache.get_cache()
                total_time = time.time() - start
                logger.info(f"get_top10_articles_hive_mapper: [缓存命中] 耗时 {total_time:.3f}s")
                return result
            
            # 缓存失效或不存在，查询 Hive
            logger.info("get_top10_articles_hive_mapper: 缓存失效，从 Hive 重新查询")
            query_start = time.time()
            with hive_conn.cursor() as cursor:
                # 直接查表，不用视图
                cursor.execute(f"SELECT {', '.join(columns)} FROM articles ORDER BY views DESC LIMIT 10")
                top10 = cursor.fetchall()
            
            query_time = time.time() - query_start
            
            # ✓ 转换为字典
            result = [dict(zip(columns, r)) for r in top10]
            
            # ✓ 更新缓存（记录版本号）
            self._article_cache.set_cache(result, hive_conn)
            
            total_time = time.time() - start
            logger.info(f"get_top10_articles_hive_mapper: 获取连接耗时 {pool_time:.3f}s, 查询耗时 {query_time:.3f}s, 缓存更新, 总耗时 {total_time:.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"get_top10_articles_hive_mapper 失败: {e}")
            raise
        finally:
            # ✓ 归还连接到池
            if hive_conn:
                self._hive_pool.return_connection(hive_conn)

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