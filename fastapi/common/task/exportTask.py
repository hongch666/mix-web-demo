import os
import csv
import subprocess
from pyhive import hive
from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session
from config import get_db
from common.utils import fileLogger as logger
from api.mapper.articleMapper import get_all_articles_mapper
from apscheduler.schedulers.base import BaseScheduler

from config import load_config

def export_articles_to_csv_and_hive():
    db: Session = next(get_db())
    try:
        # 1. 导出到本地csv
        articles = get_all_articles_mapper(db)
        if not articles:
            logger.warning("没有文章数据可导出")
            return
        # 2. 写入csv
        FILE_PATH: str = load_config("files")["excel_path"]
        csv_file = os.path.normpath(os.path.join(os.getcwd(), FILE_PATH, "articles.csv"))
        csv_file = os.path.abspath(csv_file)
        os.makedirs(os.path.dirname(csv_file), exist_ok=True)
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 写表头
            writer.writerow([
                'id', 'title', 'tags', 'status', 'views', 'create_at', 'update_at', 'content', 'user_id', 'sub_category_id'
            ])
            for a in articles:
                writer.writerow([
                    getattr(a, 'id', ''),
                    str(getattr(a, 'title', '')).replace('\n', ' ').replace(',', ';'),
                    str(getattr(a, 'tags', '')).replace('\n', ' ').replace(',', ';'),
                    getattr(a, 'status', ''),
                    getattr(a, 'views', ''),
                    getattr(a, 'create_at', ''),
                    getattr(a, 'update_at', ''),
                    str(getattr(a, 'content', '')).replace('\n', ' ').replace(',', ';'),
                    getattr(a, 'user_id', ''),
                    getattr(a, 'sub_category_id', '')
                ])
        logger.info(f"文章表已导出到本地csv: {csv_file}")

        # 3. 尝试LOAD DATA到hive
        try:
            hive_host = load_config("database")["hive"]["host"]
            hive_port = load_config("database")["hive"]["port"]
            hive_db = load_config("database")["hive"]["database"]
            hive_table = load_config("database")["hive"]["table"]
            hive_container = load_config("database")["hive"]["container"]
            # 复制csv到hive容器
            container_path = f"/tmp/{os.path.basename(csv_file)}"
            copy_cmd = f"docker cp {csv_file} {hive_container}:{container_path}"
            subprocess.run(copy_cmd, shell=True, check=True, capture_output=True)
            logger.info(f"已将csv复制到hive容器: {container_path}")
            # 连接hive
            conn = hive.Connection(host=hive_host, port=hive_port, database=hive_db)
            cursor = conn.cursor()
            # 删除旧表，重建表
            cursor.execute(f"DROP TABLE IF EXISTS {hive_table}")
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {hive_table} (
                id INT,
                title STRING,
                tags STRING,
                status INT,
                views INT,
                create_at STRING,
                update_at STRING,
                content STRING,
                user_id INT,
                sub_category_id INT
            )
            ROW FORMAT DELIMITED
            FIELDS TERMINATED BY ','
            STORED AS TEXTFILE
            TBLPROPERTIES ('skip.header.line.count'='1')
            """
            cursor.execute(create_sql)
            logger.info("hive表已创建")
            # 加载数据
            load_sql = f"LOAD DATA LOCAL INPATH '{container_path}' OVERWRITE INTO TABLE {hive_table}"
            cursor.execute(load_sql)
            logger.info("csv已LOAD DATA到hive表")
            cursor.close()
            conn.close()
        except Exception as hive_e:
            logger.error(f"连接hive或LOAD DATA失败，仅导出csv: {hive_e}")
    except Exception as e:
        logger.error(f"定时任务导出文章表失败: {e}")

def start_scheduler() -> BaseScheduler:
    scheduler: BackgroundScheduler = BackgroundScheduler()
    # 每1小时执行一次
    scheduler.add_job(export_articles_to_csv_and_hive, 'interval', hours=1)
    scheduler.start()
    logger.info("定时任务调度器已启动")
    return scheduler