import os
import csv
import subprocess
from typing import Optional, Callable, Any, List, Dict
from pyhive import hive
from sqlmodel import Session
from config import load_config
from common.utils import fileLogger as logger

def export_articles_to_csv_and_hive(
    article_mapper: Optional[Any] = None,
    user_mapper: Optional[Any] = None,
    db_factory: Optional[Callable[[], Session]] = None,
    article_cache: Optional[Any] = None,
    category_cache: Optional[Any] = None,
    publish_time_cache: Optional[Any] = None,
    statistics_cache: Optional[Any] = None,
) -> None:
    """
    可注入的导出任务。
    - article_mapper: ArticleMapper 实例（应包含 get_all_articles 和 get_users_by_ids 方法）
    - db_factory: callable，返回一个 DB Session（例如 next(get_db) 的封装）
    - *_cache: 缓存实例，用于清除导出后的缓存
    如果未传入，会在运行时按原有方式自动获取 provider。
    """
    # 延迟导入 provider，避免导入环节的循环或重资源开销
    if article_mapper is None:
        from api.mapper.articleMapper import get_article_mapper
        article_mapper = get_article_mapper()

    # 如果没有单独的 user_mapper，尝试从 userMapper provider 获取，否则回退到 article_mapper
    if user_mapper is None:
        try:
            from api.mapper.userMapper import get_user_mapper
            user_mapper = get_user_mapper()
        except Exception:
            user_mapper = article_mapper

    if db_factory is None:
        from config import get_db as _get_db
        # 封装成 callable，调用时执行 next(get_db())
        db_factory = lambda: next(_get_db())

    # 如果缓存实例未传入，延迟导入
    if article_cache is None:
        try:
            from common.cache import get_article_cache
            article_cache = get_article_cache()
        except Exception:
            article_cache = None
    
    if category_cache is None:
        try:
            from common.cache import get_category_cache
            category_cache = get_category_cache()
        except Exception:
            category_cache = None
    
    if publish_time_cache is None:
        try:
            from common.cache import get_publish_time_cache
            publish_time_cache = get_publish_time_cache()
        except Exception:
            publish_time_cache = None
    
    if statistics_cache is None:
        try:
            from common.cache import get_statistics_cache
            statistics_cache = get_statistics_cache()
        except Exception:
            statistics_cache = None

    db: Optional[Session] = None
    try:
        db = db_factory()
        # 1. 导出到本地csv
        # 兼容 mapper 的不同方法名
        if hasattr(article_mapper, 'get_all_articles'):
            article_get_all = article_mapper.get_all_articles
        elif hasattr(article_mapper, 'get_all_articles_mapper'):
            article_get_all = article_mapper.get_all_articles_mapper
        else:
            # 兜底：尝试直接调用 callable article_mapper(db)
            article_get_all = article_mapper if callable(article_mapper) else None

        if article_get_all is None:
            logger.error('article_mapper 未提供获取全部文章的方法')
            return

        # 支持传入 function 或 mapper instance
        articles = article_get_all(db) if callable(article_get_all) else []
        if not articles:
            logger.warning("没有文章数据可导出")
            return

        # 获取所有user_id（确保类型一致）
        user_ids: List[int] = [getattr(a, 'user_id', None) for a in articles if getattr(a, 'user_id', None) is not None]

        # 解析 user 查询方法，兼容不同命名
        user_get_by_ids = None
        if hasattr(user_mapper, 'get_users_by_ids'):
            user_get_by_ids = user_mapper.get_users_by_ids
        elif hasattr(user_mapper, 'get_users_by_ids_mapper'):
            user_get_by_ids = user_mapper.get_users_by_ids_mapper
        elif callable(user_mapper):
            user_get_by_ids = user_mapper

        users = user_get_by_ids(user_ids, db) if (user_ids and callable(user_get_by_ids)) else []
        user_id_to_name: Dict[int, str] = {user.id: user.name for user in users}

        # 2. 写入csv
        FILE_PATH: str = load_config("files")["excel_path"]
        csv_file = os.path.normpath(os.path.join(os.getcwd(), FILE_PATH, "articles.csv"))
        csv_file = os.path.abspath(csv_file)
        os.makedirs(os.path.dirname(csv_file), exist_ok=True)
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 写表头
            writer.writerow([
                'id', 'title', 'tags', 'status', 'views', 'create_at', 'update_at',
                'content', 'user_id', 'sub_category_id', 'username'
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
                    getattr(a, 'sub_category_id', ''),
                    user_id_to_name.get(getattr(a, 'user_id', None), '')
                ])
        logger.info(f"文章表已导出到本地csv: {csv_file}")

        # 3. 尝试COPY并LOAD DATA到hive（保持原逻辑）
        try:
            hive_cfg = load_config("database")["hive"]
            hive_host = hive_cfg["host"]
            hive_port = hive_cfg["port"]
            hive_db = hive_cfg["database"]
            hive_table = hive_cfg["table"]
            hive_container = hive_cfg["container"]

            # 复制csv到hive容器
            container_path = f"/tmp/{os.path.basename(csv_file)}"
            copy_cmd = f"docker cp {csv_file} {hive_container}:{container_path}"
            subprocess.run(copy_cmd, shell=True, check=True, capture_output=True)
            logger.info(f"已将csv复制到hive容器: {container_path}")

            # 连接 hive 并重建表、加载数据
            conn = hive.Connection(host=hive_host, port=hive_port, database=hive_db)
            cursor = conn.cursor()
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
            load_sql = f"LOAD DATA LOCAL INPATH '{container_path}' OVERWRITE INTO TABLE {hive_table}"
            cursor.execute(load_sql)
            logger.info("csv已LOAD DATA到hive表")
            cursor.close()
            conn.close()
        except Exception as hive_e:
            logger.error(f"连接hive或LOAD DATA失败，仅导出csv: {hive_e}")

        # 清除所有相关缓存
        try:
            if article_cache is not None and hasattr(article_cache, 'clear_all'):
                article_cache.clear_all()
            if category_cache is not None and hasattr(category_cache, 'clear_all'):
                category_cache.clear_all()
            if publish_time_cache is not None and hasattr(publish_time_cache, 'clear_all'):
                publish_time_cache.clear_all()
            if statistics_cache is not None and hasattr(statistics_cache, 'clear_all'):
                statistics_cache.clear_all()
            logger.info("已清除所有缓存: top10文章、分类文章数、月份文章数、统计信息")
        except Exception as cache_e:
            logger.error(f"清除缓存失败: {cache_e}")

    except Exception as e:
        logger.error(f"定时任务导出文章表失败: {e}")
    finally:
        # 关闭 db session（如果支持）
        try:
            if db is not None and hasattr(db, "close"):
                db.close()
        except Exception:
            pass
