from common.client import call_remote_service
from pyhive import hive
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

import os
from config import load_config
from entity.po import Article

async def get_top10_articles_hive_mapper():
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

async def get_top10_articles_spark_mapper():
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

async def get_top10_articles_db_mapper():
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

async def get_all_articles_mapper() -> list[Article]:
    # 使用Spring部分获取日志数据
    result = await call_remote_service(
        service_name="spring",
        path="/articles/list",
        method="GET"
    )
    return result["data"]["list"]