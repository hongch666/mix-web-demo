import hashlib
from datetime import datetime
from typing import Optional, Callable, Any, List
from sqlmodel import Session
from config import load_config
from common.agent import get_rag_tools
from common.utils import fileLogger as logger

# Redis 键名
_VECTOR_SYNC_TIME_KEY = "vector_sync:last_sync_time"
_ARTICLE_CONTENT_HASH_PREFIX = "article_content_hash:"


def _get_redis_client():
    """获取 Redis 客户端"""
    try:
        from common.cache import get_redis_client
        return get_redis_client()
    except ImportError:
        # 备用方案：使用 redis 库直接连接
        try:
            import redis
            cfg = load_config("database")["redis"]
            return redis.Redis(
                host=cfg.get("host", "localhost"),
                port=cfg.get("port", 6379),
                db=cfg.get("db", 0),
                decode_responses=True
            )
        except Exception as e:
            logger.error(f"无法连接到 Redis: {e}")
            return None


def _compute_article_hash(article: Any) -> str:
    """计算文章内容的 hash 值（只包含需要同步的字段）"""
    try:
        # 只对标题和内容计算hash（这两个字段最重要）
        title = str(getattr(article, 'title', '')).strip()
        content = str(getattr(article, 'content', '')).strip()
        tags = str(getattr(article, 'tags', '')).strip()
        
        # 组合成统一格式用于hash计算
        hash_str = f"{title}||{content}||{tags}"
        new_hash = hashlib.md5(hash_str.encode()).hexdigest()
        logger.debug(f"计算文章 hash 完成: title='{title[:20]}...', hash={new_hash}")
        return new_hash
    except Exception as e:
        logger.error(f"计算文章 hash 失败: {e}")
        return ""


def _get_article_content_hash(article_id: int) -> Optional[str]:
    """从 Redis 获取文章内容 hash"""
    try:
        redis_client = _get_redis_client()
        if redis_client is None:
            return None
        
        hash_value = redis_client.get(f"{_ARTICLE_CONTENT_HASH_PREFIX}{article_id}")
        return hash_value
    except Exception as e:
        logger.warning(f"从 Redis 读取文章 hash 失败: {e}")
        return None


def _save_article_content_hash(article_id: int, hash_value: str) -> None:
    """将文章内容 hash 永久保存到 Redis（不设置TTL）"""
    try:
        redis_client = _get_redis_client()
        if redis_client is None:
            logger.warning(f"Redis 连接失败，无法保存文章 {article_id} 的 hash")
            return
        
        # 永久保存 hash（不设置过期时间）
        redis_client.set(
            f"{_ARTICLE_CONTENT_HASH_PREFIX}{article_id}",
            hash_value
        )
        logger.debug(f"已保存文章 {article_id} 的 hash 到 Redis: {hash_value}")
    except Exception as e:
        logger.error(f"保存文章 {article_id} 的 hash 到 Redis 失败: {e}")


def _get_last_sync_time() -> Optional[datetime]:
    """从 Redis 获取上次同步时间"""
    try:
        redis_client = _get_redis_client()
        if redis_client is None:
            logger.warning("Redis 连接失败，无法获取上次同步时间")
            return None
        
        timestamp_str = redis_client.get(_VECTOR_SYNC_TIME_KEY)
        if timestamp_str:
            return datetime.fromisoformat(timestamp_str)
    except Exception as e:
        logger.warning(f"从 Redis 读取同步时间戳失败: {e}")
    
    return None


def _save_sync_time(sync_time: datetime) -> None:
    """将同步时间永久保存到 Redis（不设置TTL）"""
    try:
        redis_client = _get_redis_client()
        if redis_client is None:
            logger.error("Redis 连接失败，无法保存同步时间戳")
            return
        
        # 永久保存时间戳（不设置过期时间）
        redis_client.set(
            _VECTOR_SYNC_TIME_KEY,
            sync_time.isoformat()
        )
        logger.info(f"已保存同步时间戳到 Redis: {sync_time.isoformat()}")
    except Exception as e:
        logger.error(f"保存同步时间戳到 Redis 失败: {e}")


def _get_changed_articles(articles: List[Any], last_sync_time: Optional[datetime]) -> List[Any]:
    """
    筛选出内容实际变化的已发布文章（基于hash对比）
    
    Args:
        articles: 全部文章列表
        last_sync_time: 上次同步时间（仅用于首次同步的判断）
    
    Returns:
        内容有变化的已发布文章列表
    """
    # 先筛选已发布的文章
    published_articles = [a for a in articles if getattr(a, 'status', 0) == 1]
    
    if last_sync_time is None:
        # 首次同步，返回所有已发布文章
        logger.info("首次同步向量库，将同步所有已发布文章")
        # 同时为这些文章保存 hash 值
        for article in published_articles:
            article_id = getattr(article, 'id', 0)
            if article_id:
                current_hash = _compute_article_hash(article)
                if current_hash:
                    _save_article_content_hash(article_id, current_hash)
        return published_articles
    
    changed_articles = []
    for article in published_articles:
        article_id = getattr(article, 'id', 0)
        if not article_id:
            continue
        
        # 计算当前内容的 hash
        current_hash = _compute_article_hash(article)
        if not current_hash:
            logger.warning(f"无法计算文章 {article_id} 的 hash")
            continue
        
        # 从 Redis 获取上次保存的 hash
        cached_hash = _get_article_content_hash(article_id)
        logger.info(f"文章 {article_id}: 缓存hash={cached_hash}, 当前hash={current_hash}")
        
        # 比对 hash 值
        if cached_hash is None:
            # 缓存中没有（可能是新文章），视为有变化
            logger.info(f"文章 {article_id} 在缓存中不存在，视为新增，将同步")
            changed_articles.append(article)
            # 保存当前 hash
            if current_hash:
                _save_article_content_hash(article_id, current_hash)
        elif cached_hash != current_hash:
            # hash 不相同，说明内容有变化
            logger.info(f"文章 {article_id} 内容已变化，将同步 (旧: {cached_hash}, 新: {current_hash})")
            changed_articles.append(article)
            # 更新 hash 值
            if current_hash:
                _save_article_content_hash(article_id, current_hash)
        else:
            # hash 相同，内容未变化
            logger.debug(f"文章 {article_id} 内容未变化，跳过同步")
    
    return changed_articles


def export_article_vectors_to_postgres(
    article_mapper: Optional[Any] = None,
    mysql_db_factory: Optional[Callable[[], Session]] = None,
    enable_incremental_sync: bool = True,
) -> None:
    """
    定时同步 MySQL 文章到 PostgreSQL 向量库（使用LangChain）
    支持增量同步模式，带重试机制
    
    Args:
        article_mapper: ArticleMapper 实例
        mysql_db_factory: MySQL 数据库会话工厂
        enable_incremental_sync: 是否启用增量同步（仅同步有变更的文章）
    """
    # 延迟导入，避免循环依赖
    if article_mapper is None:
        from api.mapper.articleMapper import get_article_mapper
        article_mapper = get_article_mapper()
    
    if mysql_db_factory is None:
        from config import get_db as _get_db
        mysql_db_factory = lambda: next(_get_db())
    
    # 导入RAG工具
    try:
        rag_tools = get_rag_tools()
    except ImportError as e:
        logger.error(f"RAG工具未找到: {e}")
        return
    
    mysql_db: Optional[Session] = None
    sync_start_time = datetime.now()
    
    try:
        mysql_db = mysql_db_factory()
        
        logger.info("开始同步文章向量到 PostgreSQL...")
        
        # 1. 获取所有文章
        if hasattr(article_mapper, 'get_all_articles'):
            articles = article_mapper.get_all_articles(mysql_db)
        elif hasattr(article_mapper, 'get_all_articles_mapper'):
            articles = article_mapper.get_all_articles_mapper(mysql_db)
        else:
            logger.error("ArticleMapper 未提供获取文章的方法")
            return
        
        if not articles:
            logger.info("没有文章数据")
            return
        
        # 2. 增量同步：筛选出变更的文章
        if enable_incremental_sync:
            last_sync_time = _get_last_sync_time()
            changed_articles = _get_changed_articles(articles, last_sync_time)
            
            if not changed_articles:
                logger.info("没有文章内容变更，跳过向量库同步")
                return
            
            logger.info(f"增量同步模式：检测到 {len(changed_articles)} 篇文章有变更")
            sync_articles = changed_articles
        else:
            # 全量同步模式
            published_articles = [a for a in articles if getattr(a, 'status', 0) == 1]
            if not published_articles:
                logger.info("没有已发布的文章需要同步")
                return
            logger.info(f"全量同步模式：找到 {len(published_articles)} 篇已发布文章")
            sync_articles = published_articles
        
        # 3. 批量处理文章
        batch_size = 10  # 每批处理 10 篇文章
        total_synced = 0
        total_errors = 0
        failed_articles = []
        max_retries = 3
        retry_delay = 2  # 秒
        
        for i in range(0, len(sync_articles), batch_size):
            batch = sync_articles[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            # 提取文章信息
            article_ids = [getattr(a, 'id', 0) for a in batch]
            titles = [getattr(a, 'title', '') for a in batch]
            contents = [getattr(a, 'content', '') for a in batch]
            
            # 构建元数据
            metadata_list = []
            for a in batch:
                metadata_list.append({
                    "user_id": getattr(a, 'user_id', None),
                    "tags": getattr(a, 'tags', ''),
                    "status": getattr(a, 'status', 0),
                    "views": getattr(a, 'views', 0),
                    "create_at": str(getattr(a, 'create_at', '')),
                    "update_at": str(getattr(a, 'update_at', ''))
                })
            
            # 重试逻辑
            retry_count = 0
            batch_success = False
            last_error = None
            
            while retry_count < max_retries and not batch_success:
                try:
                    # 增量同步时，先删除旧向量再插入新向量
                    if enable_incremental_sync and hasattr(rag_tools, 'delete_articles_from_vector_store'):
                        try:
                            rag_tools.delete_articles_from_vector_store(article_ids)
                            logger.debug(f"已删除旧向量 (IDs: {article_ids})")
                        except Exception as e:
                            logger.warning(f"删除旧向量失败，将覆盖: {e}")
                    
                    # 使用RAG工具添加到向量存储
                    result = rag_tools.add_articles_to_vector_store(
                        article_ids=article_ids,
                        titles=titles,
                        contents=contents,
                        metadata_list=metadata_list
                    )
                    
                    # 检查结果是否成功（如果返回字符串包含"失败"则视为失败）
                    result_str = str(result)
                    if "失败" in result_str or "error" in result_str.lower():
                        last_error = result_str
                        retry_count += 1
                        if retry_count < max_retries:
                            logger.warning(f"批次 {batch_num} 同步返回失败信息，准备重试 ({retry_count}/{max_retries}): {result}")
                            import time
                            time.sleep(retry_delay)
                            continue
                        else:
                            raise Exception(f"重试 {max_retries} 次后仍然失败: {result}")
                    
                    total_synced += len(batch)
                    batch_success = True
                    logger.info(f"批次 {batch_num} 同步成功: {result}")
                    
                except Exception as e:
                    last_error = str(e)
                    retry_count += 1
                    
                    if retry_count < max_retries:
                        logger.warning(f"批次 {batch_num} 同步失败，准备重试 ({retry_count}/{max_retries}): {e}")
                        import time
                        time.sleep(retry_delay)
                    else:
                        total_errors += len(batch)
                        failed_articles.extend(article_ids)
                        logger.error(f"批次 {batch_num} 重试 {max_retries} 次仍然失败，放弃同步: {e}")
        
        # 4. 只有当有成功的同步时才保存时间戳
        if enable_incremental_sync and total_synced > 0:
            _save_sync_time(sync_start_time)
        
        sync_mode = "增量" if enable_incremental_sync else "全量"
        logger.info(
            f"{sync_mode}同步完成！成功: {total_synced} 篇，失败: {total_errors} 篇"
        )
        
        if failed_articles:
            logger.warning(f"失败的文章 ID: {failed_articles}")
        
    except Exception as e:
        logger.error(f"同步文章向量任务失败: {e}")
    finally:
        # 关闭数据库会话
        try:
            if mysql_db is not None and hasattr(mysql_db, "close"):
                mysql_db.close()
        except Exception:
            pass


def initialize_article_content_hash_cache(
    article_mapper: Optional[Any] = None,
    mysql_db_factory: Optional[Callable[[], Session]] = None,
) -> None:
    """
    为所有已发布的文章初始化内容 hash 缓存。
    用于生产环境已有大量文章和向量库数据，但缺少 hash 缓存的场景。
    此操作只生成 hash，不进行向量同步。
    
    Args:
        article_mapper: ArticleMapper 实例
        mysql_db_factory: MySQL 数据库会话工厂
    """
    # 延迟导入，避免循环依赖
    if article_mapper is None:
        from api.mapper.articleMapper import get_article_mapper
        article_mapper = get_article_mapper()
    
    if mysql_db_factory is None:
        from config import get_db as _get_db
        mysql_db_factory = lambda: next(_get_db())
    
    mysql_db: Optional[Session] = None
    
    try:
        mysql_db = mysql_db_factory()
        
        logger.info("开始初始化文章内容 hash 缓存...")
        
        # 1. 获取所有文章
        if hasattr(article_mapper, 'get_all_articles'):
            articles = article_mapper.get_all_articles(mysql_db)
        elif hasattr(article_mapper, 'get_all_articles_mapper'):
            articles = article_mapper.get_all_articles_mapper(mysql_db)
        else:
            logger.error("ArticleMapper 未提供获取文章的方法")
            return
        
        if not articles:
            logger.info("没有文章数据")
            return
        
        # 2. 筛选已发布的文章
        published_articles = [a for a in articles if getattr(a, 'status', 0) == 1]
        
        if not published_articles:
            logger.info("没有已发布的文章需要初始化")
            return
        
        logger.info(f"找到 {len(published_articles)} 篇已发布文章，开始计算并缓存 hash...")
        
        # 3. 为每篇文章计算并保存 hash
        total_initialized = 0
        total_skipped = 0
        
        for article in published_articles:
            article_id = getattr(article, 'id', 0)
            if not article_id:
                continue
            
            # 检查是否已存在 hash 缓存
            existing_hash = _get_article_content_hash(article_id)
            if existing_hash is not None:
                # hash 已存在，跳过
                total_skipped += 1
                continue
            
            # 计算当前内容的 hash
            current_hash = _compute_article_hash(article)
            if not current_hash:
                logger.warning(f"无法计算文章 {article_id} 的 hash")
                continue
            
            # 保存 hash 到 Redis
            _save_article_content_hash(article_id, current_hash)
            total_initialized += 1
            
            # 每 100 篇输出一次进度
            if total_initialized % 100 == 0:
                logger.info(f"已初始化 {total_initialized} 篇文章的 hash 缓存...")
        
        logger.info(
            f"hash 缓存初始化完成！新增: {total_initialized} 篇，已存在: {total_skipped} 篇"
        )
        
        # 4. 初始化完成后，也要保存同步时间戳，以便下次增量同步时能识别这是有历史数据的
        _save_sync_time(datetime.now())
        logger.info("已设置同步时间戳，下次同步将使用增量模式")
        
    except Exception as e:
        logger.error(f"初始化文章 hash 缓存失败: {e}")
    finally:
        # 关闭数据库会话
        try:
            if mysql_db is not None and hasattr(mysql_db, "close"):
                mysql_db.close()
        except Exception:
            pass
