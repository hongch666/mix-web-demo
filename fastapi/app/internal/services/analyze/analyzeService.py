import asyncio
import os
import time
import uuid
from datetime import datetime
from functools import lru_cache
from typing import Any, Awaitable, Callable, Dict, List, Optional

from app.core.base import Constants, Logger
from app.core.config import load_config
from app.core.db import get_db
from app.core.errors import BusinessException
from app.internal.cache import (
    ArticleCache,
    CategoryCache,
    PublishTimeCache,
    StatisticsCache,
    WordcloudCache,
    get_article_cache,
    get_category_cache,
    get_publish_time_cache,
    get_statistics_cache,
    get_wordcloud_cache,
)
from app.internal.crud import (
    ArticleLogMapper,
    ArticleMapper,
    CategoryMapper,
    CollectMapper,
    LikeMapper,
    UserMapper,
    get_article_mapper,
    get_articlelog_mapper,
    get_category_mapper,
    get_collect_mapper,
    get_like_mapper,
    get_user_mapper,
)
from dateutil.relativedelta import relativedelta
from openpyxl import Workbook
from sqlalchemy.orm import Session
from wordcloud import WordCloud

from fastapi import Depends

from ..external.client import call_remote_service


class AnalyzeService:
    """文章数据分析 Service"""

    def __init__(
        self,
        articleMapper: Optional[ArticleMapper] = None,
        articleLogMapper: Optional[ArticleLogMapper] = None,
        userMapper: Optional[UserMapper] = None,
        categoryMapper: Optional[CategoryMapper] = None,
        likeMapper: Optional[LikeMapper] = None,
        collectMapper: Optional[CollectMapper] = None,
        article_cache: Optional[ArticleCache] = None,
        category_cache: Optional[CategoryCache] = None,
        publish_time_cache: Optional[PublishTimeCache] = None,
        statistics_cache: Optional[StatisticsCache] = None,
        wordcloud_cache: Optional[WordcloudCache] = None,
    ):
        self.articleMapper: Optional[ArticleMapper] = articleMapper
        self.articleLogMapper: Optional[ArticleLogMapper] = articleLogMapper
        self.userMapper: Optional[UserMapper] = userMapper
        self.categoryMapper: Optional[CategoryMapper] = categoryMapper
        self.likeMapper: Optional[LikeMapper] = likeMapper
        self.collectMapper: Optional[CollectMapper] = collectMapper
        # 注入缓存对象
        self._article_cache: Optional[ArticleCache] = article_cache
        self._category_cache: Optional[CategoryCache] = category_cache
        self._publish_time_cache: Optional[PublishTimeCache] = publish_time_cache
        self._statistics_cache: Optional[StatisticsCache] = statistics_cache
        self._wordcloud_cache: Optional[WordcloudCache] = wordcloud_cache
        self._singleflight_locks: Dict[str, asyncio.Lock] = {}
        self._singleflight_guard: asyncio.Lock = asyncio.Lock()

    async def _get_singleflight_lock(self, key: str) -> asyncio.Lock:
        async with self._singleflight_guard:
            lock = self._singleflight_locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                self._singleflight_locks[key] = lock
            return lock

    async def _run_with_singleflight(
        self,
        key: str,
        cache_getter: Callable[[], Any],
        loader: Callable[[], Awaitable[Any]],
    ) -> Any:
        """使用 asyncio.Lock 合并同 key 的并发缓存回源请求，避免缓存雪崩时同时打到数据库。"""
        cached_result = await cache_getter()
        if cached_result is not None:
            return cached_result

        lock = await self._get_singleflight_lock(key)
        async with lock:
            cached_result = await cache_getter()
            if cached_result is not None:
                Logger.info(f"[singleflight] key={key} 命中回填缓存，复用首个请求结果")
                return cached_result

            Logger.info(f"[singleflight] key={key} 开始执行缓存回源")
            return await loader()

    async def _get_top10_cached(self) -> Optional[List[Dict[str, Any]]]:
        ch_conn = None
        try:
            ch_conn = await asyncio.to_thread(
                self.articleMapper.get_clickhouse_connection
            )
            return await self._article_cache.get(ch_conn)
        except Exception as e:
            Logger.debug(f"_get_top10_cached 失败: {e}")
            return None
        finally:
            if ch_conn:
                await asyncio.to_thread(
                    self.articleMapper.return_clickhouse_connection, ch_conn
                )

    async def _get_wordcloud_cached(self) -> Optional[str]:
        try:
            return await self._wordcloud_cache.get()
        except Exception as e:
            Logger.debug(f"_get_wordcloud_cached 失败: {e}")
            return None

    async def _get_statistics_cached(self) -> Optional[Dict[str, Any]]:
        try:
            return await self._statistics_cache.get()
        except Exception as e:
            Logger.debug(f"_get_statistics_cached 失败: {e}")
            return None

    async def _get_category_article_count_cached(
        self,
    ) -> Optional[List[Dict[str, Any]]]:
        ch_conn = None
        try:
            ch_conn = await asyncio.to_thread(
                self.articleMapper.get_clickhouse_connection
            )
            return await self._category_cache.get(ch_conn)
        except Exception as e:
            Logger.debug(f"_get_category_article_count_cached 失败: {e}")
            return None
        finally:
            if ch_conn:
                await asyncio.to_thread(
                    self.articleMapper.return_clickhouse_connection, ch_conn
                )

    async def _get_monthly_publish_count_cached(self) -> Optional[List[Dict[str, Any]]]:
        ch_conn = None
        try:
            ch_conn = await asyncio.to_thread(
                self.articleMapper.get_clickhouse_connection
            )
            return await self._publish_time_cache.get(ch_conn)
        except Exception as e:
            Logger.debug(f"_get_monthly_publish_count_cached 失败: {e}")
            return None
        finally:
            if ch_conn:
                await asyncio.to_thread(
                    self.articleMapper.return_clickhouse_connection, ch_conn
                )

    async def get_top10_articles_service_sf(
        self, db: Session = Depends(get_db)
    ) -> List[Dict[str, Any]]:
        return await self._run_with_singleflight(
            "analyze:top10",
            self._get_top10_cached,
            lambda: self.get_top10_articles_service(db),
        )

    async def get_wordcloud_service_sf(self) -> str:
        return await self._run_with_singleflight(
            "analyze:wordcloud",
            self._get_wordcloud_cached,
            self.get_wordcloud_service,
        )

    async def get_article_statistics_service_sf(
        self, db: Session = Depends(get_db)
    ) -> Dict[str, Any]:
        return await self._run_with_singleflight(
            "analyze:statistics",
            self._get_statistics_cached,
            lambda: self.get_article_statistics_service(db),
        )

    async def get_category_article_count_service_sf(
        self, db: Session = Depends(get_db)
    ) -> List[Dict[str, Any]]:
        return await self._run_with_singleflight(
            "analyze:category_article_count",
            self._get_category_article_count_cached,
            lambda: self.get_category_article_count_service(db),
        )

    async def get_monthly_publish_count_service_sf(
        self, db: Session = Depends(get_db)
    ) -> List[Dict[str, Any]]:
        return await self._run_with_singleflight(
            "analyze:monthly_publish_count",
            self._get_monthly_publish_count_cached,
            lambda: self.get_monthly_publish_count_service(db),
        )

    @classmethod
    def create_for_scheduler(cls) -> "AnalyzeService":
        """为调度器创建 AnalyzeService 实例（手动注入所有依赖）"""
        return cls(
            articleMapper=get_article_mapper(),
            articleLogMapper=get_articlelog_mapper(),
            userMapper=get_user_mapper(),
            categoryMapper=get_category_mapper(),
            likeMapper=get_like_mapper(),
            collectMapper=get_collect_mapper(),
            article_cache=get_article_cache(),
            category_cache=get_category_cache(),
            publish_time_cache=get_publish_time_cache(),
            statistics_cache=get_statistics_cache(),
            wordcloud_cache=get_wordcloud_cache(),
        )

    async def get_top10_articles_service(
        self, db: Session = Depends(get_db)
    ) -> List[Dict[str, Any]]:
        """
        获取 Top10 文章服务

        流程:
        1. 先尝试从缓存获取（L1本地 + L2 Redis）
        2. 缓存未命中时，按优先级查询: ClickHouse → DB
        3. 查询成功后更新缓存
        """
        articles: Optional[List[Any]] = None
        ch_conn = None
        data_source = None
        start = time.time()
        try:
            try:
                ch_conn = await asyncio.to_thread(
                    self.articleMapper.get_clickhouse_connection
                )
                cached_result = await self._article_cache.get(ch_conn)
                if cached_result:
                    total_time = time.time() - start
                    Logger.info(
                        f"get_top10_articles_service: [缓存命中] 耗时 {total_time:.3f}s"
                    )
                    return cached_result
            except Exception as cache_e:
                Logger.debug(f"缓存获取失败，将查询数据源: {cache_e}")

            Logger.info(Constants.TOP10_CACHE_MISS)

            try:
                articles = await asyncio.to_thread(
                    self.articleMapper.get_top10_articles_clickhouse_mapper
                )
                if articles and isinstance(articles[0], dict):
                    data_source = "ClickHouse"
                    Logger.info(Constants.TOP10_CLICKHOUSE_GET)
            except Exception as ch_e:
                Logger.warning(
                    f"get_top10_articles_service: ClickHouse 查询失败，降级为 DB: {ch_e}"
                )

            if not articles or len(articles) == 0:
                articles = await asyncio.to_thread(
                    self.articleMapper.get_top10_articles_db_mapper, db
                )
                data_source = "DB"
                Logger.info(Constants.TOP10_DB_SOURCE)

            if articles and isinstance(articles[0], dict):
                user_ids = [
                    article.get("user_id")
                    for article in articles
                    if article.get("user_id")
                ]
                if user_ids:
                    users = await asyncio.to_thread(
                        self.userMapper.get_users_by_ids_mapper, user_ids, db
                    )
                    user_id_to_name = {user.id: user.name for user in users}
                    for article in articles:
                        article["username"] = user_id_to_name.get(
                            article.get("user_id")
                        )

                for article in articles:
                    if article.get("create_at") and hasattr(
                        article["create_at"], "isoformat"
                    ):
                        article["create_at"] = article["create_at"].isoformat()
                    if article.get("update_at") and hasattr(
                        article["update_at"], "isoformat"
                    ):
                        article["update_at"] = article["update_at"].isoformat()

                result = articles
            else:
                user_ids = [article.user_id for article in articles]
                users = await asyncio.to_thread(
                    self.userMapper.get_users_by_ids_mapper, user_ids, db
                )
                user_id_to_name = {user.id: user.name for user in users}
                result = [
                    {
                        "id": article.id,
                        "title": article.title,
                        "content": article.content,
                        "user_id": article.user_id,
                        "username": user_id_to_name.get(article.user_id),
                        "tags": article.tags,
                        "status": article.status,
                        "create_at": article.create_at.isoformat()
                        if article.create_at
                        else None,
                        "update_at": article.update_at.isoformat()
                        if article.update_at
                        else None,
                        "views": article.views,
                        "sub_category_id": getattr(article, "sub_category_id", None),
                    }
                    for article in articles
                ]

            if ch_conn and result:
                try:
                    await self._article_cache.set(result, ch_conn)
                    total_time = time.time() - start
                    Logger.info(
                        f"get_top10_articles_service: {data_source} 数据已更新缓存，总耗时 {total_time:.3f}s"
                    )
                except Exception as cache_e:
                    Logger.warning(f"更新缓存失败: {cache_e}")

            return result
        finally:
            if ch_conn:
                await asyncio.to_thread(
                    self.articleMapper.return_clickhouse_connection, ch_conn
                )

    async def get_keywords_dic(self) -> Dict[str, int]:
        all_keywords: List[
            str
        ] = await self.articleLogMapper.get_search_keywords_articlelog_mapper()
        keywords_dic: Dict[str, int] = {}
        for keyword in all_keywords:
            if keyword in keywords_dic:
                keywords_dic[keyword] += 1
            else:
                keywords_dic[keyword] = 1
        return keywords_dic

    def generate_wordcloud(self, keywords_dic: Dict[str, int]) -> None:
        if len(keywords_dic) == 0:
            raise BusinessException(Constants.KEYWORDS_EMPTY)
        wc_config = load_config("wordcloud")
        FONT_PATH: str = wc_config["font_path"]
        WIDTH: int = wc_config["width"]
        HEIGHT: int = wc_config["height"]
        BACKGROUND_COLOR: str = wc_config["background_color"]
        wc = WordCloud(
            font_path=FONT_PATH,
            width=WIDTH,
            height=HEIGHT,
            background_color=BACKGROUND_COLOR,
        )
        wc.generate_from_frequencies(keywords_dic)
        FILE_PATH: str = load_config("files")["pic_path"]
        wc.to_file(
            os.path.normpath(
                os.path.join(os.getcwd(), FILE_PATH, "search_keywords_wordcloud.png")
            )
        )
        Logger.info(Constants.WORDCLOUD_GENERATION_SUCCESS)

    async def upload_file(self, file_path: str, oss_path: str) -> str:
        """远程调用 NestJS 上传文件到 OSS。"""

        try:
            result: Dict[str, Any] = await call_remote_service(
                service_name="nestjs",
                path="/upload",
                method="POST",
                json={
                    "local_file": file_path,
                    "oss_file": oss_path,
                },
                retries=3,
            )
            oss_url: str = str(result.get("data", ""))
            Logger.info(f"文件上传成功，OSS地址: {oss_url}")
            Logger.info(f"本地文件路径: {file_path}, OSS路径: {oss_path}")
            return oss_url
        except Exception as e:
            Logger.error(f"远程上传文件到OSS失败: {str(e)}")
            raise

    async def upload_wordcloud_to_oss(self) -> str:
        FILE_PATH: str = load_config("files")["pic_path"]
        # 使用 UUID 生成随机文件名
        random_filename = f"{uuid.uuid4()}.png"
        oss_url: str = await self.upload_file(
            file_path=os.path.normpath(
                os.path.join(os.getcwd(), FILE_PATH, Constants.WORDCLOUD_FILENAME)
            ),
            oss_path=f"pic/{random_filename}",
        )
        return oss_url

    async def get_wordcloud_service(self) -> str:
        """
        获取词云图OSS URL服务

        流程:
        1. 先尝试从缓存获取（L1本地 + L2 Redis）
        2. 缓存未命中时，生成词云图并上传到OSS
        3. 将OSS URL缓存到两级缓存（L1本地5分钟 + L2 Redis 24小时）
        """
        start = time.time()

        # ========== 步骤1: 尝试从缓存获取（二级缓存） ==========
        try:
            cached_url = await self._wordcloud_cache.get()
            if cached_url:
                elapsed = time.time() - start
                Logger.info(f"get_wordcloud_service: [缓存命中] 耗时 {elapsed:.3f}s")
                return cached_url
        except Exception as cache_e:
            Logger.debug(f"获取词云图缓存失败，将重新生成: {cache_e}")

        # ========== 步骤2: 缓存未命中，生成词云图并上传 ==========
        Logger.info(Constants.WORDCLOUD_CACHE_FETCH_FAILED)
        # 获取关键词字典
        keywords_dic = await self.get_keywords_dic()
        # 生成词云图
        await asyncio.to_thread(self.generate_wordcloud, keywords_dic)
        # 上传到OSS
        oss_url = await self.upload_wordcloud_to_oss()

        # ========== 步骤3: 缓存到两级缓存 ==========
        try:
            await self._wordcloud_cache.set(oss_url)
            elapsed = time.time() - start
            Logger.info(
                f"get_wordcloud_service: 词云图已生成并缓存到L1+L2，总耗时 {elapsed:.3f}s"
            )
        except Exception as cache_e:
            Logger.warning(f"缓存词云图URL失败: {cache_e}")

        return oss_url

    async def export_articles_to_excel(self, db: Session = Depends(get_db)) -> str:
        FILE_PATH: str = load_config("files")["excel_path"]
        file_path = os.path.normpath(
            os.path.join(
                os.getcwd(), FILE_PATH, Constants.EXPORT_ARTICLES_EXCEL_FILENAME
            )
        )

        headers = [
            "id",
            "title",
            "content",
            "username",
            "tags",
            "status",
            "create_at",
            "update_at",
            "views",
            "sub_category_name",
            "category_name",
            "like_count",
            "collect_count",
            "author_follow_count",
        ]

        workbook = Workbook(write_only=True)
        worksheet = workbook.create_sheet(title="Sheet1")
        worksheet.append([Constants.EXPORT_ARTICLES_EXCEL_TIP])
        worksheet.append(headers)

        def _export_to_excel() -> int:
            total_rows = 0
            for batch in self.articleMapper.iter_articles_for_excel_export_mapper(db):
                for item in batch:
                    worksheet.append(
                        [
                            item.get("id"),
                            item.get("title"),
                            item.get("content"),
                            item.get("username"),
                            item.get("tags"),
                            item.get("status"),
                            item.get("create_at").isoformat()
                            if item.get("create_at")
                            else None,
                            item.get("update_at").isoformat()
                            if item.get("update_at")
                            else None,
                            item.get("views"),
                            item.get("sub_category_name"),
                            item.get("category_name"),
                            item.get("like_count"),
                            item.get("collect_count"),
                            item.get("author_follow_count"),
                        ]
                    )
                    total_rows += 1

            workbook.save(file_path)
            return total_rows

        total_rows = await asyncio.to_thread(_export_to_excel)
        Logger.info(f"文章表已导出到 {file_path}，共写入 {total_rows} 条记录")
        return file_path

    async def upload_excel_to_oss(self, file_path: str) -> str:
        random_filename = f"{uuid.uuid4()}.xlsx"
        oss_url: str = await self.upload_file(
            file_path=file_path,
            oss_path=f"excel/{random_filename}",
        )
        return oss_url

    async def get_article_statistics_service(
        self, db: Session = Depends(get_db)
    ) -> Dict[str, Any]:
        """
        获取文章统计信息服务
        合并 mapper 层的方法，返回完整的统计数据

        流程:
        1. 先尝试从缓存获取（L1本地 + L2 Redis）
        2. 缓存未命中时，查询DB
        3. 查询成功后更新缓存

        返回字段:
        - total_views: 总阅读量
        - total_articles: 文章总数
        - active_authors: 活跃作者数
        - average_views: 文章平均阅读次数
        - total_likes: 总点赞数（新增，直接DB查询）
        - average_likes: 文章平均点赞数（新增，直接DB查询）
        - total_collects: 总收藏数（新增，直接DB查询）
        - average_collects: 文章平均收藏数（新增，直接DB查询）
        """
        start = time.time()
        # ========== 步骤1: 尝试从缓存获取 ==========
        try:
            cached_result = await self._statistics_cache.get()
            if cached_result:
                total_time = time.time() - start
                Logger.info(
                    f"get_article_statistics_service: [缓存命中] 耗时 {total_time:.3f}s"
                )
                return cached_result
        except Exception as cache_e:
            Logger.debug(f"缓存获取失败，将查询数据源: {cache_e}")

        # ========== 步骤2: 缓存未命中，查询DB ==========
        Logger.info(Constants.STATISTICS_CACHE_FETCH_FAILED)

        def _load_statistics() -> Dict[str, Any]:
            total_views = self.articleMapper.get_total_views_mapper(db)
            total_articles = self.articleMapper.get_total_articles_mapper(db)
            active_authors = self.articleMapper.get_active_authors_mapper(db)
            average_views = self.articleMapper.get_average_views_mapper(db)
            total_likes = self.likeMapper.get_total_likes_mapper(db)
            average_likes = self.likeMapper.get_average_likes_mapper(db)
            total_collects = self.collectMapper.get_total_collects_mapper(db)
            average_collects = self.collectMapper.get_average_collects_mapper(db)

            return {
                "total_views": total_views,
                "total_articles": total_articles,
                "active_authors": active_authors,
                "average_views": average_views,
                "total_likes": total_likes,
                "average_likes": average_likes,
                "total_collects": total_collects,
                "average_collects": average_collects,
            }

        statistics = await asyncio.to_thread(_load_statistics)

        # ========== 步骤3: 更新缓存 ==========
        try:
            await self._statistics_cache.set(statistics)
            total_time = time.time() - start
            Logger.info(
                f"get_article_statistics_service: DB 数据已更新缓存，总耗时 {total_time:.3f}s"
            )
        except Exception as cache_e:
            Logger.warning(f"更新缓存失败: {cache_e}")

        Logger.info(f"获取文章统计信息: {statistics}")
        return statistics

    async def get_category_article_count_service(
        self, db: Session = Depends(get_db)
    ) -> List[Dict[str, Any]]:
        """
        获取按大分类统计的文章数量服务

        流程:
        1. 从ClickHouse查询文章数据（按子分类分组）
        2. 从MySQL获取所有大分类信息
        3. 将文章数据按大分类聚合（没有文章的分类返回0）
        4. 按文章数量排序
        5. 使用缓存优化性能

        返回: 所有大分类及其文章总数（从多到少排序）
        """
        category_data = None
        ch_conn = None
        data_source = None
        start = time.time()
        try:
            # ========== 步骤1: 尝试从缓存获取 ==========
            try:
                ch_conn = await asyncio.to_thread(
                    self.articleMapper.get_clickhouse_connection
                )
                cached_result = await self._category_cache.get(ch_conn)
                if cached_result:
                    total_time = time.time() - start
                    Logger.info(
                        f"get_category_article_count_service: [缓存命中] 耗时 {total_time:.3f}s"
                    )
                    return cached_result
            except Exception as cache_e:
                Logger.debug(f"缓存获取失败，将查询数据源: {cache_e}")

            # ========== 步骤2: 缓存未命中，按优先级查询数据源 ==========
            Logger.info(Constants.CATEGORY_STATISTICS_CACHE_FETCH_FAILED)

            def _load_category_statistics() -> tuple[List[Dict[str, Any]], str]:
                local_category_data = None
                local_data_source = "DB"

                try:
                    local_category_data = self.articleMapper.get_category_article_count_clickhouse_mapper()
                    local_data_source = "ClickHouse"
                    Logger.info(Constants.CATEGORY_STATISTICS_CLICKHOUSE_GET)
                except Exception as ch_e:
                    Logger.warning(
                        f"get_category_article_count_service: ClickHouse 查询失败，降级为 DB: {ch_e}"
                    )
                    local_data_source = "DB"

                if not local_category_data:
                    local_category_data = (
                        self.articleMapper.get_category_article_count_db_mapper(db)
                    )
                    local_data_source = "DB"
                    Logger.info(Constants.CATEGORY_STATISTICS_DB_SOURCE)

                all_categories = self.categoryMapper.get_all_categories_mapper(db)
                subcategories = (
                    self.categoryMapper.get_subcategories_with_parent_mapper(db)
                )
                sub_cat_map = {sc["id"]: sc for sc in subcategories}

                parent_category_count = {}
                for category in all_categories:
                    parent_category_count[category.id] = {
                        "category_id": category.id,
                        "category_name": category.name,
                        "article_count": 0,
                    }

                for item in local_category_data:
                    sub_cat_id = item["sub_category_id"]
                    sub_cat_info = sub_cat_map.get(sub_cat_id, {})

                    parent_id = sub_cat_info.get("category_id")
                    if parent_id and parent_id in parent_category_count:
                        parent_category_count[parent_id]["article_count"] += item[
                            "count"
                        ]

                result = list(parent_category_count.values())
                result.sort(key=lambda x: x["article_count"], reverse=True)

                non_zero_count = len([c for c in result if c["article_count"] > 0])
                Logger.info(
                    f"get_category_article_count_service: 获取 {len(result)} 个大分类，有文章的分类数: {non_zero_count}"
                )

                return result, local_data_source

            result, data_source = await asyncio.to_thread(_load_category_statistics)

            # ========== 步骤7: 更新缓存 ==========
            if ch_conn and result:
                try:
                    await self._category_cache.set(result, ch_conn)
                    total_time = time.time() - start
                    Logger.info(
                        f"get_category_article_count_service: {data_source} 数据已更新缓存，总耗时 {total_time:.3f}s"
                    )
                except Exception as cache_e:
                    Logger.warning(f"更新缓存失败: {cache_e}")

            return result
        finally:
            if ch_conn:
                await asyncio.to_thread(
                    self.articleMapper.return_clickhouse_connection, ch_conn
                )

    async def get_monthly_publish_count_service(
        self, db: Session = Depends(get_db)
    ) -> List[Dict[str, Any]]:
        """
        获取按月份统计的文章发布数量服务

        流程:
        1. 从ClickHouse查询最近6个月的文章发布数据
        2. 从当前月份向前推6个月，补充缺失的月份为零值
        3. 按月份排序
        4. 使用缓存优化性能
        """
        publish_data = None
        ch_conn = None
        data_source = None
        start = time.time()
        try:
            # ========== 步骤1: 尝试从缓存获取 ==========
            try:
                ch_conn = await asyncio.to_thread(
                    self.articleMapper.get_clickhouse_connection
                )
                cached_result = await self._publish_time_cache.get(ch_conn)
                if cached_result:
                    total_time = time.time() - start
                    Logger.info(
                        f"get_monthly_publish_count_service: [缓存命中] 耗时 {total_time:.3f}s"
                    )
                    return cached_result
            except Exception as cache_e:
                Logger.debug(f"缓存获取失败，将查询数据源: {cache_e}")

            # ========== 步骤2: 缓存未命中，按优先级查询数据源 ==========
            Logger.info(Constants.MONTHLY_STATISTICS_CACHE_FETCH_FAILED)

            def _load_monthly_statistics() -> tuple[List[Dict[str, Any]], str]:
                local_publish_data = None
                local_data_source = "DB"

                try:
                    local_publish_data = (
                        self.articleMapper.get_monthly_publish_count_clickhouse_mapper()
                    )
                    local_data_source = "ClickHouse"
                    Logger.info(Constants.MONTHLY_STATISTICS_CLICKHOUSE_GET)
                except Exception as ch_e:
                    Logger.warning(
                        f"get_monthly_publish_count_service: ClickHouse 查询失败，降级为 DB: {ch_e}"
                    )

                if not local_publish_data:
                    local_publish_data = (
                        self.articleMapper.get_monthly_publish_count_db_mapper(db)
                    )
                    local_data_source = "DB"
                    Logger.info(Constants.MONTHLY_STATISTICS_DB_SOURCE)

                now = datetime.now()
                expected_months = []
                for i in range(5, -1, -1):
                    month_date = now - relativedelta(months=i)
                    expected_months.append(month_date.strftime("%Y-%m"))

                data_dict = {
                    item["year_month"]: item["count"] for item in local_publish_data
                }

                result = []
                for month in expected_months:
                    result.append(
                        {"year_month": month, "count": data_dict.get(month, 0)}
                    )

                result.sort(key=lambda x: x["year_month"], reverse=False)
                Logger.info(
                    f"get_monthly_publish_count_service: 获取过去6个月中 {len(result)} 个月份数据，有文章的月份数: {len([r for r in result if r['count'] > 0])}"
                )
                return result, local_data_source

            result, data_source = await asyncio.to_thread(_load_monthly_statistics)

            # ========== 步骤5: 更新缓存 ==========
            if ch_conn and result:
                try:
                    await self._publish_time_cache.set(result, ch_conn)
                    total_time = time.time() - start
                    Logger.info(
                        f"get_monthly_publish_count_service: {data_source} 数据已更新缓存，总耗时 {total_time:.3f}s"
                    )
                except Exception as cache_e:
                    Logger.warning(f"更新缓存失败: {cache_e}")

            return result
        finally:
            if ch_conn:
                await asyncio.to_thread(
                    self.articleMapper.return_clickhouse_connection, ch_conn
                )


@lru_cache()
def get_analyze_service(
    articleMapper: ArticleMapper = Depends(get_article_mapper),
    articleLogMapper: ArticleLogMapper = Depends(get_articlelog_mapper),
    userMapper: UserMapper = Depends(get_user_mapper),
    categoryMapper: CategoryMapper = Depends(get_category_mapper),
    likeMapper: LikeMapper = Depends(get_like_mapper),
    collectMapper: CollectMapper = Depends(get_collect_mapper),
    article_cache: ArticleCache = Depends(get_article_cache),
    category_cache: CategoryCache = Depends(get_category_cache),
    publish_time_cache: PublishTimeCache = Depends(get_publish_time_cache),
    statistics_cache: StatisticsCache = Depends(get_statistics_cache),
    wordcloud_cache: WordcloudCache = Depends(get_wordcloud_cache),
) -> AnalyzeService:
    return AnalyzeService(
        articleMapper,
        articleLogMapper,
        userMapper,
        categoryMapper,
        likeMapper,
        collectMapper,
        article_cache,
        category_cache,
        publish_time_cache,
        statistics_cache,
        wordcloud_cache,
    )
