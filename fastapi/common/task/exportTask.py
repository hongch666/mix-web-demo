import os
import csv
import subprocess
from functools import partial
from typing import Optional, Callable, Any, List, Dict

from pyhive import hive
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import BaseScheduler
from sqlmodel import Session

from config import load_config
from common.utils import fileLogger as logger

def export_articles_to_csv_and_hive(
    article_mapper: Optional[Any] = None,
    user_mapper: Optional[Any] = None,
    db_factory: Optional[Callable[[], Session]] = None,
) -> None:
    """
    可注入的导出任务。
    - article_mapper: ArticleMapper 实例（应包含 get_all_articles 和 get_users_by_ids 方法）
    - db_factory: callable，返回一个 DB Session（例如 next(get_db) 的封装）
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

    except Exception as e:
        logger.error(f"定时任务导出文章表失败: {e}")
    finally:
        # 关闭 db session（如果支持）
        try:
            if db is not None and hasattr(db, "close"):
                db.close()
        except Exception:
            pass


def export_article_vectors_to_postgres(
    article_mapper: Optional[Any] = None,
    vector_mapper: Optional[Any] = None,
    embedding_service: Optional[Any] = None,
    mysql_db_factory: Optional[Callable[[], Session]] = None,
    pg_db_factory: Optional[Callable[[], Session]] = None,
) -> None:
    """
    定时同步 MySQL 文章到 PostgreSQL 向量库
    
    Args:
        article_mapper: ArticleMapper 实例
        vector_mapper: VectorMapper 实例
        embedding_service: EmbeddingService 实例
        mysql_db_factory: MySQL 数据库会话工厂
        pg_db_factory: PostgreSQL 数据库会话工厂
    """
    # 延迟导入，避免循环依赖
    if article_mapper is None:
        from api.mapper.articleMapper import get_article_mapper
        article_mapper = get_article_mapper()
    
    if vector_mapper is None:
        try:
            from api.mapper.vectorMapper import get_vector_mapper
            vector_mapper = get_vector_mapper()
        except ImportError:
            logger.error("VectorMapper 未找到，跳过向量同步")
            return
    
    if embedding_service is None:
        try:
            from api.service.embeddingService import get_embedding_service
            embedding_service = get_embedding_service()
        except ImportError:
            logger.error("EmbeddingService 未找到，跳过向量同步")
            return
    
    if mysql_db_factory is None:
        from config import get_db as _get_db
        mysql_db_factory = lambda: next(_get_db())
    
    if pg_db_factory is None:
        try:
            from config.postgres import get_pg_db as _get_pg_db
            pg_db_factory = lambda: next(_get_pg_db())
        except ImportError:
            logger.error("PostgreSQL 配置未找到，跳过向量同步")
            return
    
    mysql_db: Optional[Session] = None
    pg_db: Optional[Session] = None
    
    try:
        mysql_db = mysql_db_factory()
        pg_db = pg_db_factory()
        
        logger.info("开始同步文章向量到 PostgreSQL...")
        
        # 1. 获取最近更新的文章
        if hasattr(article_mapper, 'get_all_articles'):
            articles = article_mapper.get_all_articles(mysql_db)
        elif hasattr(article_mapper, 'get_all_articles_mapper'):
            articles = article_mapper.get_all_articles_mapper(mysql_db)
        else:
            logger.error("ArticleMapper 未提供获取文章的方法")
            return
        
        if not articles:
            logger.info("没有文章需要同步")
            return
        
        # 2. 获取已存在文章的内容哈希（用于快速对比）
        existing_hash = vector_mapper.get_existing_articles_hash(pg_db)
        logger.info(f"已获取 {len(existing_hash)} 篇已存在文章的哈希值")
        
        # 3. 筛选需要同步的文章（内容有变化或新文章）
        articles_to_sync = []
        skipped_count = 0
        
        for article in articles:
            article_id = getattr(article, 'id', 0)
            title = getattr(article, 'title', '')
            content_preview = getattr(article, 'content', '')[:500]
            
            # 构建当前文章的内容标识
            current_content_key = f"{title}|{content_preview}"
            
            # 如果文章不存在或内容有变化，才需要同步
            if article_id not in existing_hash or existing_hash[article_id] != current_content_key:
                articles_to_sync.append(article)
            else:
                skipped_count += 1
        
        logger.info(f"需要同步 {len(articles_to_sync)} 篇文章，跳过 {skipped_count} 篇未变化的文章")
        
        if not articles_to_sync:
            logger.info("所有文章都已是最新，无需同步")
            return
        
        # 4. 批量处理需要同步的文章
        sync_count = 0
        error_count = 0
        batch_size = 50  # 每批处理 50 篇文章
        
        for i in range(0, len(articles_to_sync), batch_size):
            batch = articles_to_sync[i:i + batch_size]
            
            # 构建文本列表
            texts = [
                f"{getattr(a, 'title', '')} {getattr(a, 'content', '')[:500]}"
                for a in batch
            ]
            
            try:
                # 批量向量化（只计算需要更新的文章）
                embeddings = embedding_service.encode_batch(texts)
                
                # 批量更新到 PostgreSQL
                for article, embedding in zip(batch, embeddings):
                    try:
                        vector_mapper.upsert_article_vector(
                            pg_db,
                            article_id=getattr(article, 'id', 0),
                            title=getattr(article, 'title', ''),
                            content_preview=getattr(article, 'content', '')[:500],
                            embedding=embedding
                        )
                        sync_count += 1
                    except Exception as e:
                        error_count += 1
                        logger.error(f"同步文章 {getattr(article, 'id', 'unknown')} 失败: {e}")
                
                logger.info(f"已同步批次 {i // batch_size + 1}，共 {len(batch)} 篇文章")
                
            except Exception as e:
                error_count += len(batch)
                logger.error(f"批量向量化失败: {e}")
        
        logger.info(
            f"向量同步完成！成功: {sync_count} 篇，失败: {error_count} 篇，跳过: {skipped_count} 篇"
        )
        
    except Exception as e:
        logger.error(f"同步文章向量任务失败: {e}")
    finally:
        # 关闭数据库会话
        try:
            if mysql_db is not None and hasattr(mysql_db, "close"):
                mysql_db.close()
        except Exception:
            pass
        
        try:
            if pg_db is not None and hasattr(pg_db, "close"):
                pg_db.close()
        except Exception:
            pass


def start_scheduler(
    article_mapper: Optional[Any] = None,
    user_mapper: Optional[Any] = None,
    vector_mapper: Optional[Any] = None,
    embedding_service: Optional[Any] = None,
    db_factory: Optional[Callable[[], Session]] = None,
    mysql_db_factory: Optional[Callable[[], Session]] = None,
    pg_db_factory: Optional[Callable[[], Session]] = None,
) -> BaseScheduler:
    """
    启动调度器，可把依赖注入进来（用于测试或容器式管理）。
    例如：
      start_scheduler(
          article_mapper=get_article_mapper(), 
          db_factory=lambda: next(get_db()),
          pg_db_factory=lambda: next(get_pg_db())
      )
    """
    scheduler: BackgroundScheduler = BackgroundScheduler()

    # 任务1：导出文章到 CSV 和 Hive
    export_job_func = partial(
        export_articles_to_csv_and_hive, 
        article_mapper=article_mapper, 
        user_mapper=user_mapper, 
        db_factory=db_factory or mysql_db_factory
    )
    # 每1小时执行一次
    scheduler.add_job(export_job_func, 'interval', hours=1, id='export_articles')
    
    # 任务2：同步文章向量到 PostgreSQL
    sync_vector_job_func = partial(
        export_article_vectors_to_postgres,
        article_mapper=article_mapper,
        vector_mapper=vector_mapper,
        embedding_service=embedding_service,
        mysql_db_factory=mysql_db_factory or db_factory,
        pg_db_factory=pg_db_factory
    )
    # 每2小时执行一次向量同步（可根据需要调整频率）
    scheduler.add_job(sync_vector_job_func, 'interval', hours=2, id='sync_vectors')
    
    scheduler.start()
    logger.info("定时任务调度器已启动：")
    logger.info("  - 文章导出任务：每 1 小时执行一次")
    logger.info("  - 向量同步任务：每 10 分钟执行一次")
    return scheduler