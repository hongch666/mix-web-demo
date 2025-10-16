from functools import lru_cache
from sqlmodel import Session, select
from pyhive import hive
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import os
from config import load_config
from entity.po import Article

class ArticleMapper:

    def get_top10_articles_hive_mapper(self):
        columns = [
            "id", "title", "tags", "status", "views", "create_at", "update_at", "content", "user_id", "sub_category_id", "username"
        ]
        hive_host = load_config("database")["hive"]["host"]
        hive_port = load_config("database")["hive"]["port"]
        hive_db = load_config("database")["hive"]["database"]
        hive_conn = hive.Connection(host=hive_host, port=hive_port, database=hive_db)
        with hive_conn.cursor() as cursor:
            cursor.execute(f"SELECT {', '.join(columns)} FROM articles ORDER BY views DESC LIMIT 10")
            top10 = cursor.fetchall()
        hive_conn.close()
        return [dict(zip(columns, r)) for r in top10]

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
    
@lru_cache()
def get_article_mapper() -> ArticleMapper:
    return ArticleMapper()