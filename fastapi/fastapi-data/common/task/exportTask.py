import os
import csv
import subprocess
from pyhive import hive
from apscheduler.schedulers.background import BackgroundScheduler
from common.utils import fileLogger as logger
from api.mapper import ArticleMapper, UserMapper, get_article_mapper, get_user_mapper
from apscheduler.schedulers.base import BaseScheduler

from config import load_config

async def export_articles_to_csv_and_hive():
    try:
        # 1. 获取文章数据
        articleMapper: ArticleMapper = get_article_mapper()
        userMapper: UserMapper = get_user_mapper()
        articles = await articleMapper.get_all_articles_mapper()
        if not articles:
            logger.warning("没有文章数据可导出")
            return
        # 获取所有user_id
        user_ids = [a["userId"] for a in articles if a["userId"] is not None]
        users = await userMapper.get_users_by_ids_mapper(user_ids) if user_ids else []
        user_id_to_name = {user["id"]: user["name"] for user in users}
        # 2. 写入csv
        FILE_PATH: str = load_config("files")["excel_path"]
        csv_file = os.path.normpath(os.path.join(os.getcwd(), FILE_PATH, "articles.csv"))
        csv_file = os.path.abspath(csv_file)
        os.makedirs(os.path.dirname(csv_file), exist_ok=True)
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 写表头
            writer.writerow([
                'id', 'title', 'tags', 'status', 'views', 'create_at', 'update_at', 'content', 'user_id', 'sub_category_id','username'
            ])
            for a in articles:
                # 获取时间字段，尝试多种可能的字段名
                create_at = (getattr(a, 'create_at', '') if hasattr(a, 'create_at') else 
                           a.get('create_at', '') or a.get('createAt', '') or a.get('created_at', ''))
                update_at = (getattr(a, 'update_at', '') if hasattr(a, 'update_at') else 
                           a.get('update_at', '') or a.get('updateAt', '') or a.get('updated_at', ''))
                
                writer.writerow([
                    getattr(a, 'id', '') if hasattr(a, 'id') else a.get('id', ''),
                    str(getattr(a, 'title', '') if hasattr(a, 'title') else a.get('title', '')).replace('\n', ' ').replace(',', ';'),
                    str(getattr(a, 'tags', '') if hasattr(a, 'tags') else a.get('tags', '')).replace('\n', ' ').replace(',', ';'),
                    getattr(a, 'status', '') if hasattr(a, 'status') else a.get('status', ''),
                    getattr(a, 'views', '') if hasattr(a, 'views') else a.get('views', ''),
                    str(create_at),
                    str(update_at),
                    str(getattr(a, 'content', '') if hasattr(a, 'content') else a.get('content', '')).replace('\n', ' ').replace(',', ';'),
                    getattr(a, 'user_id', '') if hasattr(a, 'user_id') else a.get('user_id', '') or a.get('userId', ''),
                    getattr(a, 'sub_category_id', '') if hasattr(a, 'sub_category_id') else a.get('sub_category_id', '') or a.get('subCategoryId', ''),
                    user_id_to_name[getattr(a, 'user_id', '') if hasattr(a, 'user_id') else a.get('user_id', '') or a.get('userId', '')]
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
                sub_category_id INT,
                username STRING
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