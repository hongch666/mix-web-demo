import asyncio
import hashlib
from datetime import datetime
from typing import Any, Optional

from app.core.base import Logger
from app.core.constants import Messages, RedisKeys
from app.internal.agents.langsmith import get_langsmith_context
from app.internal.cache import get_redis_client
from app.internal.clients import SpringClient, get_spring_client
from app.internal.crud import (
    VectorMapper,
    get_vector_embeddings,
    get_vector_store_mapper,
)


def _get_redis_client() -> Optional[Any]:
    """获取 Redis 客户端"""
    return get_redis_client()


def _get_article_field(article: Any, field: str, default: Any = "") -> Any:
    """兼容 dict 和 ORM 对象的字段访问"""
    if isinstance(article, dict):
        return article.get(field, default)
    return getattr(article, field, default)


def _compute_article_hash(article: Any) -> str:
    """计算文章内容的 hash 值（只包含需要同步的字段）"""
    try:
        # 只对标题和内容计算hash（这两个字段最重要）
        title = str(_get_article_field(article, "title", "")).strip()
        content = str(_get_article_field(article, "content", "")).strip()
        tags = str(_get_article_field(article, "tags", "")).strip()

        # 组合成统一格式用于hash计算
        hash_str = f"{title}||{content}||{tags}"
        new_hash = hashlib.md5(hash_str.encode()).hexdigest()
        Logger.debug(Messages.VECTOR_ARTICLE_HASH_COMPUTED(title[:20], new_hash))
        return new_hash
    except Exception as e:
        Logger.error(Messages.VECTOR_ARTICLE_HASH_COMPUTE_FAILED(e))
        return ""


async def _get_article_content_hash(article_id: int) -> Optional[str]:
    """从 Redis 获取文章内容 hash"""
    try:
        redis_client: Optional[Any] = _get_redis_client()
        if redis_client is None:
            return None

        hash_value: Optional[str] = await redis_client.get(
            RedisKeys.article_content_hash(article_id)
        )
        return hash_value
    except Exception as e:
        Logger.warning(Messages.VECTOR_REDIS_HASH_READ_FAILED(e))
        return None


async def _save_article_content_hash(article_id: int, hash_value: str) -> None:
    """将文章内容 hash 永久保存到 Redis（不设置TTL）"""
    try:
        redis_client: Optional[Any] = _get_redis_client()
        if redis_client is None:
            Logger.warning(Messages.VECTOR_REDIS_SAVE_HASH_UNAVAILABLE(article_id))
            return

        # 永久保存 hash（不设置过期时间）
        await redis_client.set(RedisKeys.article_content_hash(article_id), hash_value)
        Logger.debug(Messages.VECTOR_ARTICLE_HASH_SAVED(article_id, hash_value))
    except Exception as e:
        Logger.error(Messages.VECTOR_ARTICLE_HASH_SAVE_FAILED(article_id, e))


async def _get_last_sync_time() -> Optional[datetime]:
    """从 Redis 获取上次同步时间"""
    try:
        redis_client: Optional[Any] = _get_redis_client()
        if redis_client is None:
            Logger.warning(Messages.REDIS_CONNECTION_FAILED_MESSAGE)
            return None

        timestamp_str: Optional[str] = await redis_client.get(
            RedisKeys.VECTOR_SYNC_TIME
        )
        if timestamp_str:
            return datetime.fromisoformat(timestamp_str)
    except Exception as e:
        Logger.warning(Messages.VECTOR_REDIS_SYNC_TIME_READ_FAILED(e))

    return None


async def _save_sync_time(sync_time: datetime) -> None:
    """将同步时间永久保存到 Redis（不设置TTL）"""
    try:
        redis_client: Optional[Any] = _get_redis_client()
        if redis_client is None:
            Logger.error(Messages.REDIS_CONNECTION_SAVE_FAILED_MESSAGE)
            return

        # 永久保存时间戳（不设置过期时间）
        await redis_client.set(RedisKeys.VECTOR_SYNC_TIME, sync_time.isoformat())
        Logger.info(Messages.VECTOR_SYNC_TIME_SAVED(sync_time.isoformat()))
    except Exception as e:
        Logger.error(Messages.VECTOR_SYNC_TIME_SAVE_FAILED(e))


async def _get_changed_articles(
    articles: list[Any], last_sync_time: Optional[datetime]
) -> list[Any]:
    """
    筛选出内容实际变化的已发布文章（基于hash对比）

    Args:
        articles: 全部文章列表
        last_sync_time: 上次同步时间（仅用于首次同步的判断）

    Returns:
        内容有变化的已发布文章列表
    """
    # 先筛选已发布的文章
    published_articles: list[Any] = [
        a for a in articles if _get_article_field(a, "status", 0) == 1
    ]

    if last_sync_time is None:
        # 首次同步，返回所有已发布文章
        Logger.info(Messages.FIRST_TIME_SYNC_MESSAGE)
        # 同时为这些文章保存 hash 值
        for article in published_articles:
            article_id = _get_article_field(article, "id", 0)
            if article_id:
                current_hash: str = _compute_article_hash(article)
                if current_hash:
                    await _save_article_content_hash(article_id, current_hash)
        return published_articles

    changed_articles: list[Any] = []
    for article in published_articles:
        article_id = _get_article_field(article, "id", 0)
        if not article_id:
            continue

        # 计算当前内容的 hash
        current_hash: str = _compute_article_hash(article)
        if not current_hash:
            Logger.warning(Messages.VECTOR_ARTICLE_HASH_MISSING(article_id))
            continue

        # 从 Redis 获取上次保存的 hash
        cached_hash: Optional[str] = await _get_article_content_hash(article_id)
        Logger.info(
            Messages.VECTOR_ARTICLE_HASH_COMPARE(article_id, cached_hash, current_hash)
        )

        # 比对 hash 值
        if cached_hash is None:
            # 缓存中没有（可能是新文章），视为有变化
            Logger.info(Messages.VECTOR_ARTICLE_NEW_FOUND(article_id))
            changed_articles.append(article)
            # 保存当前 hash
            if current_hash:
                await _save_article_content_hash(article_id, current_hash)
        elif cached_hash != current_hash:
            # hash 不相同，说明内容有变化
            Logger.info(
                Messages.VECTOR_ARTICLE_CONTENT_CHANGED(
                    article_id, cached_hash, current_hash
                )
            )
            changed_articles.append(article)
            # 更新 hash 值
            if current_hash:
                await _save_article_content_hash(article_id, current_hash)
        else:
            # hash 相同，内容未变化
            Logger.debug(Messages.VECTOR_ARTICLE_UNCHANGED(article_id))

    return changed_articles


async def _remove_stale_vectors(vector_mapper: VectorMapper, articles: list[Any]) -> int:
    """清理向量库中已删除或已下架文章残留的向量，并删除其内容 hash 缓存

    增量同步只处理仍在发布列表中的文章，已删除或已下架的文章不会被比对到，
    必须依靠本方法做差集清理，否则旧向量会一直残留并被检索召回

    差集口径为「向量库已有文章 ID - 本次拉到的发布文章 ID」，因此未发布状态
    等同于应清理；调用方必须确保传入的是完整的发布列表，否则会误删

    Args:
        vector_mapper: 向量库 Mapper
        articles: 本次拉取到的全部已发布文章

    Returns:
        删除的向量条数
    """
    published_ids: set[int] = set()
    for article in articles:
        article_id = _get_article_field(article, "id", 0)
        if article_id:
            published_ids.add(int(article_id))

    existing_ids: set[int] = await vector_mapper.list_article_ids()
    stale_ids: list[int] = sorted(existing_ids - published_ids)
    if not stale_ids:
        Logger.debug(Messages.VECTOR_NO_STALE_VECTORS())
        return 0

    Logger.info(Messages.VECTOR_STALE_VECTORS_FOUND(str(stale_ids)))
    deleted: int = await vector_mapper.delete_by_article_ids(stale_ids)

    redis_client: Optional[Any] = _get_redis_client()
    if redis_client is not None:
        await redis_client.delete(
            *[
                RedisKeys.article_content_hash(article_id)
                for article_id in stale_ids
            ]
        )

    Logger.info(Messages.VECTOR_STALE_VECTORS_CLEANED(deleted, len(stale_ids)))
    return deleted


async def _export_article_vectors_to_postgres(
    article_mapper: Optional[Any] = None,
    mysql_db_factory: Optional[Any] = None,
    enable_incremental_sync: bool = True,
) -> None:
    """
    定时同步 MySQL 文章到 PostgreSQL 向量库（使用LangChain）
    支持增量同步模式，带重试机制

    Args:
        article_mapper: ArticleMapper 实例（已废弃，保留参数以兼容旧调用）
        mysql_db_factory: MySQL 数据库会话工厂（已废弃，保留参数以兼容旧调用）
        enable_incremental_sync: 是否启用增量同步（仅同步有变更的文章）
    """
    spring_client: SpringClient = get_spring_client()

    vector_mapper: VectorMapper = get_vector_store_mapper(get_vector_embeddings())

    sync_start_time: datetime = datetime.now()
    sync_mode = "增量" if enable_incremental_sync else "全量"

    try:
        Logger.info(Messages.START_SYNC_TO_POSTGRES_MESSAGE)

        # 1. 通过SpringClient分页远程获取所有已发布文章
        expected_total: int = 0
        try:
            articles: list[Any] = []
            page: int = 1
            page_size: int = 100
            while True:
                page_result: Any = await spring_client.get_published_articles(
                    page=page, size=page_size, timeout=30
                )
                records: list[Any] = (
                    page_result.get("records", [])
                    if isinstance(page_result, dict)
                    else []
                )
                if not records:
                    break
                articles.extend(records)
                expected_total = (
                    int(page_result.get("total", 0))
                    if isinstance(page_result, dict)
                    else 0
                )
                if len(articles) >= expected_total:
                    break
                page += 1
        except Exception as e:
            Logger.error(Messages.VECTOR_SYNC_GET_ARTICLES_FAILED(e))
            return

        # 2. 清理已删除或已下架文章残留的向量
        # 差集清理要求列表必须完整：分页中途失败时未拉到的文章会被误判为已删除，进而清空其向量，因此这里以 expected_total 作为完整性判据，不完整则跳过并告警
        if len(articles) >= expected_total:
            try:
                await _remove_stale_vectors(vector_mapper, articles)
            except Exception as e:
                Logger.warning(Messages.VECTOR_STALE_CLEANUP_FAILED(e))
        else:
            Logger.warning(
                Messages.VECTOR_SKIP_CLEANUP_INCOMPLETE(len(articles), expected_total)
            )

        if not articles:
            Logger.info(Messages.NO_ARTICLES_DATA_MESSAGE)
            return

        # 3. 增量同步：筛选出变更的文章
        if enable_incremental_sync:
            last_sync_time: Optional[datetime] = await _get_last_sync_time()
            changed_articles: list[Any] = await _get_changed_articles(
                articles, last_sync_time
            )

            if not changed_articles:
                Logger.info(Messages.NO_CHANGED_ARTICLES_MESSAGE)
                return

            Logger.info(Messages.VECTOR_INCREMENTAL_SYNC_CHANGED(len(changed_articles)))
            sync_articles: list[Any] = changed_articles
        else:
            # 全量同步模式（列表接口已返回已发布文章）
            published_articles: list[Any] = [
                a for a in articles if _get_article_field(a, "status", 0) == 1
            ]
            if not published_articles:
                Logger.info(Messages.NO_PUBLISHED_ARTICLES_MESSAGE)
                return
            Logger.info(Messages.VECTOR_FULL_SYNC_FOUND(len(published_articles)))
            sync_articles: list[Any] = published_articles

        # 4. 批量处理文章
        batch_size: int = 10  # 每批处理 10 篇文章
        total_synced: int = 0
        total_errors: int = 0
        failed_articles: list[int] = []
        max_retries: int = 3
        retry_delay: int = 2  # 秒

        for i in range(0, len(sync_articles), batch_size):
            batch = sync_articles[i : i + batch_size]
            batch_num = i // batch_size + 1

            # 提取文章信息
            article_ids: list[int] = [_get_article_field(a, "id", 0) for a in batch]
            titles: list[str] = [_get_article_field(a, "title", "") for a in batch]
            contents: list[str] = [_get_article_field(a, "content", "") for a in batch]

            # 构建元数据
            metadata_list: list[dict] = []
            for a in batch:
                metadata_list.append(
                    {
                        "user_id": _get_article_field(a, "user_id", None),
                        "tags": _get_article_field(a, "tags", ""),
                        "status": _get_article_field(a, "status", 0),
                        "views": _get_article_field(a, "views", 0),
                        "create_at": str(_get_article_field(a, "create_at", "")),
                        "update_at": str(_get_article_field(a, "update_at", "")),
                    }
                )

            # LangSmith 批次边界 Trace
            with get_langsmith_context(
                name="vector.sync.batch",
                tags=["job:vector_sync", f"mode:{sync_mode}"],
                metadata={
                    "batch_num": batch_num,
                    "total_batches": (len(sync_articles) + batch_size - 1)
                    // batch_size,
                    "batch_size": len(batch),
                    "article_ids": [str(aid) for aid in article_ids],
                    "sync_mode": sync_mode,
                },
            ):
                # 重试逻辑
                retry_count: int = 0
                batch_success: bool = False

                while retry_count < max_retries and not batch_success:
                    try:
                        # 先删除旧向量再插入新向量，避免同一篇文章的历史分块长期残留
                        try:
                            await vector_mapper.delete_by_article_ids(article_ids)
                            Logger.debug(
                                Messages.VECTOR_DELETED_OLD_VECTORS(str(article_ids))
                            )
                        except Exception as e:
                            Logger.warning(Messages.VECTOR_DELETE_OLD_FAILED(e))

                        # 写入向量，失败会抛出异常并由外层重试分支接管
                        written: int = await vector_mapper.upsert_articles(
                            article_ids=article_ids,
                            titles=titles,
                            contents=contents,
                            metadata_list=metadata_list,
                        )

                        total_synced += len(batch)
                        batch_success = True
                        Logger.info(
                            Messages.VECTOR_BATCH_SYNC_SUCCESS(batch_num, str(written))
                        )

                    except Exception as e:
                        retry_count += 1

                        if retry_count < max_retries:
                            Logger.warning(
                                Messages.VECTOR_BATCH_SYNC_FAILED_RETRY(
                                    batch_num, retry_count, max_retries, e
                                )
                            )
                            await asyncio.sleep(retry_delay)
                        else:
                            total_errors += len(batch)
                            failed_articles.extend(article_ids)
                            Logger.error(
                                Messages.VECTOR_BATCH_RETRY_EXHAUSTED_ABANDON(
                                    batch_num, max_retries, e
                                )
                            )

        # 5. 只有当有成功的同步时才保存时间戳
        if enable_incremental_sync and total_synced > 0:
            await _save_sync_time(sync_start_time)

        sync_mode = "增量" if enable_incremental_sync else "全量"
        Logger.info(
            Messages.VECTOR_SYNC_COMPLETED(sync_mode, total_synced, total_errors)
        )

        if failed_articles:
            Logger.warning(Messages.VECTOR_FAILED_ARTICLE_IDS(str(failed_articles)))

    except Exception as e:
        Logger.error(Messages.VECTOR_SYNC_TASK_FAILED(e))


async def _initialize_article_content_hash_cache(
    article_mapper: Optional[Any] = None,
    mysql_db_factory: Optional[Any] = None,
) -> None:
    """
    为所有已发布的文章初始化内容 hash 缓存
    用于生产环境已有大量文章和向量库数据，但缺少 hash 缓存的场景
    此操作只生成 hash，不进行向量同步

    Args:
        article_mapper: ArticleMapper 实例（已废弃，保留参数以兼容旧调用）
        mysql_db_factory: MySQL 数据库会话工厂（已废弃，保留参数以兼容旧调用）
    """
    spring_client: SpringClient = get_spring_client()

    try:
        Logger.info(Messages.START_INITIALIZING_ARTICLE_HASH_CACHE_MESSAGE)

        # 1. 通过SpringClient分页远程获取所有已发布文章
        try:
            articles: list[Any] = []
            page: int = 1
            page_size: int = 100
            while True:
                page_result: Any = await spring_client.get_published_articles(
                    page=page, size=page_size, timeout=30
                )
                records: list[Any] = (
                    page_result.get("records", [])
                    if isinstance(page_result, dict)
                    else []
                )
                if not records:
                    break
                articles.extend(records)
                total: int = (
                    page_result.get("total", 0) if isinstance(page_result, dict) else 0
                )
                if len(articles) >= total:
                    break
                page += 1
        except Exception as e:
            Logger.error(Messages.VECTOR_HASH_INIT_GET_ARTICLES_FAILED(e))
            return

        if not articles:
            Logger.info(Messages.NO_ARTICLES_DATA_MESSAGE)
            return

        # 2. 筛选已发布的文章
        published_articles: list[Any] = [
            a for a in articles if _get_article_field(a, "status", 0) == 1
        ]

        if not published_articles:
            Logger.info(Messages.NO_PUBLISHED_ARTICLES_MESSAGE)
            return

        Logger.info(Messages.VECTOR_HASH_INIT_FOUND_ARTICLES(len(published_articles)))

        # 3. 为每篇文章计算并保存 hash
        total_initialized = 0
        total_skipped = 0

        for article in published_articles:
            article_id = _get_article_field(article, "id", 0)
            if not article_id:
                continue

            # 检查是否已存在 hash 缓存
            existing_hash: Optional[str] = await _get_article_content_hash(article_id)
            if existing_hash is not None:
                # hash 已存在，跳过
                total_skipped += 1
                continue

            # 计算当前内容的 hash
            current_hash: str = _compute_article_hash(article)
            if not current_hash:
                Logger.warning(Messages.VECTOR_ARTICLE_HASH_MISSING(article_id))
                continue

            # 保存 hash 到 Redis
            await _save_article_content_hash(article_id, current_hash)
            total_initialized += 1

            # 每 100 篇输出一次进度
            if total_initialized % 100 == 0:
                Logger.info(Messages.VECTOR_HASH_INIT_PROGRESS(total_initialized))

        Logger.info(
            Messages.VECTOR_HASH_INIT_COMPLETE(total_initialized, total_skipped)
        )

        # 4. 初始化完成后，也要保存同步时间戳，以便下次增量同步时能识别这是有历史数据的
        await _save_sync_time(datetime.now())
        Logger.info(Messages.SYNC_TIME_SET_MESSAGE)

    except Exception as e:
        Logger.error(Messages.VECTOR_HASH_INIT_FAILED(e))


async def export_article_vectors_to_postgres_async(
    article_mapper: Optional[Any] = None,
    mysql_db_factory: Optional[Any] = None,
    enable_incremental_sync: bool = True,
) -> None:
    """同步文章向量到 PostgreSQL，使用 Redis 分布式锁保证多实例部署时只有一个实例执行"""
    lock_key: str = RedisKeys.LOCK_TASK_VECTOR_SYNC
    lock_expire: int = RedisKeys.LOCK_TASK_VECTOR_SYNC_EXPIRE

    # 尝试获取分布式锁
    redis_client: Any = get_redis_client()
    lock_value: Optional[str] = await redis_client.try_lock(lock_key, lock_expire)
    if lock_value is None:
        Logger.info(Messages.REDIS_LOCK_ACQUIRE_FAIL_MESSAGE(lock_key))
        return
    Logger.info(Messages.REDIS_LOCK_ACQUIRE_SUCCESS_MESSAGE(lock_key))

    try:
        await _export_article_vectors_to_postgres(
            article_mapper,
            mysql_db_factory,
            enable_incremental_sync,
        )
    finally:
        released: bool = await redis_client.unlock(lock_key, lock_value)
        if released:
            Logger.info(Messages.REDIS_LOCK_RELEASE_SUCCESS_MESSAGE(lock_key))
        else:
            Logger.info(Messages.REDIS_LOCK_RELEASE_FAIL_MESSAGE(lock_key))


async def initialize_article_content_hash_cache_async(
    article_mapper: Optional[Any] = None,
    mysql_db_factory: Optional[Any] = None,
) -> None:
    await _initialize_article_content_hash_cache(
        article_mapper,
        mysql_db_factory,
    )
