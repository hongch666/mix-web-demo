from common.client import call_remote_service
from pyhive import hive
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

import os
from config import load_config
import traceback
from entity.po import Article

async def get_top10_articles_mapper():
    """
    优先用hive查top10，否则用pyspark分析csv，返回所有字段
    """
    FILE_PATH: str = load_config("files")["excel_path"]
    csv_file = os.path.normpath(os.path.join(os.getcwd(), FILE_PATH, "articles.csv"))
    csv_file = os.path.abspath(csv_file)
    columns = [
        "id", "title", "tags", "status", "views", "create_at", "update_at", "content", "user_id", "sub_category_id"
    ]
    # 1. 优先hive
    try:
        hive_host = load_config("database")["hive"]["host"]
        hive_port = load_config("database")["hive"]["port"]
        hive_db = load_config("database")["hive"]["database"]
        hive_conn = hive.Connection(host=hive_host, port=hive_port, database=hive_db)
        with hive_conn.cursor() as cursor:
            cursor.execute(f"SELECT {', '.join(columns)} FROM articles ORDER BY views DESC LIMIT 10")
            top10 = cursor.fetchall()
        hive_conn.close()
        if len(top10) == 0:
            raise ValueError("Hive查询结果为空")
        return [dict(zip(columns, r)) for r in top10]
    except Exception as hive_e:
        from common.utils import fileLogger
        fileLogger.warning(f"hive获取top10失败，降级为pyspark: {hive_e}")
    # 2. pyspark分析csv
    try:
        spark = SparkSession.builder.appName("ArticleTop10").getOrCreate()
        df = spark.read.option("header", True).csv(csv_file)
        df = df.withColumn("views", col("views").cast("int"))
        # 保证所有字段类型
        for c in ["id", "status", "user_id", "sub_category_id"]:
            df = df.withColumn(c, col(c).cast("int"))
        for c in ["create_at", "update_at"]:
            df = df.withColumn(c, col(c).cast("string"))
        top10_rows = df.orderBy(col("views").desc()).limit(10).collect()
        spark.stop()
        return [ {k: r[k] for k in columns} for r in top10_rows ]
    except Exception as spark_e:
        fileLogger.error(f"pyspark分析csv也失败: {spark_e}\n{traceback.format_exc()}")
        # 3. 兜底用远程服务获取数据
        try:
            articles = await get_all_articles_mapper()
            # 按views降序取前10
            sorted_articles = sorted(articles, key=lambda x: x.get("views", 0), reverse=True)[:10]
            # 确保返回格式统一
            return [
                {
                    "id": article.get("id"),
                    "title": article.get("title"),
                    "tags": article.get("tags"),
                    "status": article.get("status"),
                    "views": article.get("views"),
                    "create_at": article.get("create_at") or article.get("createAt"),
                    "update_at": article.get("update_at") or article.get("updateAt"),
                    "content": article.get("content"),
                    "user_id": article.get("user_id") or article.get("userId"),
                    "sub_category_id": article.get("sub_category_id") or article.get("subCategoryId"),
                }
                for article in sorted_articles
            ]
        except Exception as remote_e:
            fileLogger.error(f"远程服务获取数据也失败: {remote_e}")
            return []

async def get_all_articles_mapper() -> list[Article]:
    # 使用Spring部分获取日志数据
    result = await call_remote_service(
        service_name="spring",
        path="/articles/list",
        method="GET"
    )
    return result["data"]["list"]