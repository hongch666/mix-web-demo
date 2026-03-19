import asyncio
import os
import time
import uuid
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

import pandas as pd
from app.cache import (
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
from app.core import BusinessException, Constants, Logger
from app.crud import (
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
from app.db import get_db, load_config
from dateutil.relativedelta import relativedelta
from sqlmodel import Session
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

    def get_top10_articles_service(
        self, db: Session = Depends(get_db)
    ) -> List[Dict[str, Any]]:
        """
        获取 Top10 文章服务

        流程:
        1. 先尝试从缓存获取（L1本地 + L2 Redis）
        2. 缓存未命中时，按优先级查询: ClickHouse → DB
        3. 查询成功后更新缓存
        """
        articles = None
        ch_conn = None
        data_source = None
        start = time.time()

        # ========== 步骤1: 尝试从缓存获取 ==========
        try:
            ch_conn = self.articleMapper.get_clickhouse_connection()
            cached_result = self._article_cache.get(ch_conn)
            if cached_result:
                total_time = time.time() - start
                Logger.info(
                    f"get_top10_articles_service: [缓存命中] 耗时 {total_time:.3f}s"
                )
                return cached_result
        except Exception as cache_e:
            Logger.debug(f"缓存获取失败，将查询数据源: {cache_e}")

        # ========== 步骤2: 缓存未命中，按优先级查询数据源 ==========
        Logger.info(Constants.TOP10_CACHE_MISS)

        # 1.优先 ClickHouse
        try:
            articles = self.articleMapper.get_top10_articles_clickhouse_mapper()
            if articles and isinstance(articles[0], dict):
                data_source = "ClickHouse"
                Logger.info(Constants.TOP10_CLICKHOUSE_GET)
        except Exception as ch_e:
            Logger.warning(
                f"get_top10_articles_service: ClickHouse 查询失败，降级为 DB: {ch_e}"
            )

        # 2.DB 兜底
        if not articles or len(articles) == 0:
            articles = self.articleMapper.get_top10_articles_db_mapper(db)
            data_source = "DB"
            Logger.info(Constants.TOP10_DB_SOURCE)

        # ========== 步骤3: 处理查询结果并更新缓存 ==========
        # 检查返回类型，如果是字典列表（ClickHouse），直接处理
        if articles and isinstance(articles[0], dict):
            # ClickHouse 返回的字典包含 user_id，需要查询 username
            user_ids = [
                article.get("user_id") for article in articles if article.get("user_id")
            ]
            if user_ids:
                users = self.userMapper.get_users_by_ids_mapper(user_ids, db)
                user_id_to_name = {user.id: user.name for user in users}
                # 为每条记录添加 username
                for article in articles:
                    article["username"] = user_id_to_name.get(article.get("user_id"))

            # 处理日期格式
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
            # DB 返回的是对象，需要转换为字典并关联 username
            user_ids = [article.user_id for article in articles]
            users = self.userMapper.get_users_by_ids_mapper(user_ids, db)
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

        # 更新缓存
        if ch_conn and result:
            try:
                self._article_cache.set(result, ch_conn)
                total_time = time.time() - start
                Logger.info(
                    f"get_top10_articles_service: {data_source} 数据已更新缓存，总耗时 {total_time:.3f}s"
                )
            except Exception as cache_e:
                Logger.warning(f"更新缓存失败: {cache_e}")

        # 归还 ClickHouse 连接
        if ch_conn:
            self.articleMapper.return_clickhouse_connection(ch_conn)

        return result

    def get_keywords_dic(self) -> Dict[str, int]:
        all_keywords: List[str] = (
            self.articleLogMapper.get_search_keywords_articlelog_mapper()
        )
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

    def upload_file(self, file_path: str, oss_path: str) -> str:
        """远程调用NestJS上传文件到OSS"""

        async def _upload_async() -> str:
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
            oss_url: str = result.get("data", "")
            Logger.info(f"文件上传成功，OSS地址: {oss_url}")
            Logger.info(f"本地文件路径: {file_path}, OSS路径: {oss_path}")
            return oss_url

        try:
            # 在同步方法中运行异步函数
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已有事件循环运行中，则直接创建新的
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _upload_async())
                    return future.result()
            else:
                return asyncio.run(_upload_async())
        except Exception as e:
            Logger.error(f"远程上传文件到OSS失败: {str(e)}")
            raise

    def upload_wordcloud_to_oss(self) -> str:
        FILE_PATH: str = load_config("files")["pic_path"]
        # 使用 UUID 生成随机文件名
        random_filename = f"{uuid.uuid4()}.png"
        oss_url: str = self.upload_file(
            file_path=os.path.normpath(
                os.path.join(os.getcwd(), FILE_PATH, Constants.WORDCLOUD_FILENAME)
            ),
            oss_path=f"pic/{random_filename}",
        )
        return oss_url

    def get_wordcloud_service(self) -> str:
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
            cached_url = self._wordcloud_cache.get()
            if cached_url:
                elapsed = time.time() - start
                Logger.info(f"get_wordcloud_service: [缓存命中] 耗时 {elapsed:.3f}s")
                return cached_url
        except Exception as cache_e:
            Logger.debug(f"获取词云图缓存失败，将重新生成: {cache_e}")

        # ========== 步骤2: 缓存未命中，生成词云图并上传 ==========
        Logger.info(Constants.WORDCLOUD_CACHE_FETCH_FAILED)
        # 获取关键词字典
        keywords_dic = self.get_keywords_dic()
        # 生成词云图
        self.generate_wordcloud(keywords_dic)
        # 上传到OSS
        oss_url = self.upload_wordcloud_to_oss()

        # ========== 步骤3: 缓存到两级缓存 ==========
        try:
            self._wordcloud_cache.set(oss_url)
            elapsed = time.time() - start
            Logger.info(
                f"get_wordcloud_service: 词云图已生成并缓存到L1+L2，总耗时 {elapsed:.3f}s"
            )
        except Exception as cache_e:
            Logger.warning(f"缓存词云图URL失败: {cache_e}")

        return oss_url

    def export_articles_to_excel(self, db: Session = Depends(get_db)) -> str:
        FILE_PATH: str = load_config("files")["excel_path"]
        file_path = os.path.normpath(
            os.path.join(
                os.getcwd(), FILE_PATH, Constants.EXPORT_ARTICLES_EXCEL_FILENAME
            )
        )
        data = self.articleMapper.get_articles_for_excel_export_mapper(db)
        for item in data:
            item["create_at"] = (
                item["create_at"].isoformat() if item.get("create_at") else None
            )
            item["update_at"] = (
                item["update_at"].isoformat() if item.get("update_at") else None
            )
        df = pd.DataFrame(data)
        # 先写入数据
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, startrow=1)
            worksheet = writer.sheets["Sheet1"]
            worksheet.cell(row=1, column=1, value=Constants.EXPORT_ARTICLES_EXCEL_TIP)
        Logger.info(f"文章表已导出到 {file_path}")
        return file_path

    def upload_excel_to_oss(self, file_path: str) -> str:
        random_filename = f"{uuid.uuid4()}.xlsx"
        oss_url: str = self.upload_file(
            file_path=file_path,
            oss_path=f"excel/{random_filename}",
        )
        return oss_url

    def get_article_statistics_service(
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
            cached_result = self._statistics_cache.get()
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

        # 分别调用 mapper 层的方法
        total_views = self.articleMapper.get_total_views_mapper(db)
        total_articles = self.articleMapper.get_total_articles_mapper(db)
        active_authors = self.articleMapper.get_active_authors_mapper(db)
        average_views = self.articleMapper.get_average_views_mapper(db)
        total_likes = self.likeMapper.get_total_likes_mapper(db)
        average_likes = self.likeMapper.get_average_likes_mapper(db)
        total_collects = self.collectMapper.get_total_collects_mapper(db)
        average_collects = self.collectMapper.get_average_collects_mapper(db)

        # 组合结果
        statistics = {
            "total_views": total_views,
            "total_articles": total_articles,
            "active_authors": active_authors,
            "average_views": average_views,
            "total_likes": total_likes,
            "average_likes": average_likes,
            "total_collects": total_collects,
            "average_collects": average_collects,
        }

        # ========== 步骤3: 更新缓存 ==========
        try:
            self._statistics_cache.set(statistics)
            total_time = time.time() - start
            Logger.info(
                f"get_article_statistics_service: DB 数据已更新缓存，总耗时 {total_time:.3f}s"
            )
        except Exception as cache_e:
            Logger.warning(f"更新缓存失败: {cache_e}")

        Logger.info(f"获取文章统计信息: {statistics}")
        return statistics

    def get_category_article_count_service(
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

        # ========== 步骤1: 尝试从缓存获取 ==========
        try:
            ch_conn = self.articleMapper.get_clickhouse_connection()
            cached_result = self._category_cache.get(ch_conn)
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

        # 1.优先 ClickHouse
        try:
            category_data = (
                self.articleMapper.get_category_article_count_clickhouse_mapper()
            )
            data_source = "ClickHouse"
            Logger.info(Constants.CATEGORY_STATISTICS_CLICKHOUSE_GET)
        except Exception as ch_e:
            Logger.warning(
                f"get_category_article_count_service: ClickHouse 查询失败，降级为 DB: {ch_e}"
            )

        # 2.DB 兜底
        if not category_data or len(category_data) == 0:
            category_data = self.articleMapper.get_category_article_count_db_mapper(db)
            data_source = "DB"
            Logger.info(Constants.CATEGORY_STATISTICS_DB_SOURCE)

        # ========== 步骤3: 获取所有大分类信息 ==========
        all_categories = self.categoryMapper.get_all_categories_mapper(db)

        # ========== 步骤4: 获取子分类与大分类的映射关系 ==========
        subcategories = self.categoryMapper.get_subcategories_with_parent_mapper(db)
        sub_cat_map = {sc["id"]: sc for sc in subcategories}

        # ========== 步骤5: 按大分类聚合文章数（包括文章数为0的分类） ==========
        # 初始化所有大分类，文章数都是0
        parent_category_count = {}
        for category in all_categories:
            parent_category_count[category.id] = {
                "category_id": category.id,
                "category_name": category.name,
                "article_count": 0,
            }

        # 遍历文章数据，累加到对应的大分类
        for item in category_data:
            sub_cat_id = item["sub_category_id"]
            sub_cat_info = sub_cat_map.get(sub_cat_id, {})

            parent_id = sub_cat_info.get("category_id")
            if parent_id and parent_id in parent_category_count:
                parent_category_count[parent_id]["article_count"] += item["count"]

        # ========== 步骤6: 按文章数量排序（从多到少） ==========
        result = list(parent_category_count.values())
        result.sort(key=lambda x: x["article_count"], reverse=True)

        Logger.info(
            f"get_category_article_count_service: 获取 {len(result)} 个大分类，有文章的分类数: {len([c for c in result if c['article_count'] > 0])}"
        )

        # ========== 步骤7: 更新缓存 ==========
        if ch_conn and result:
            try:
                self._category_cache.set(result, ch_conn)
                total_time = time.time() - start
                Logger.info(
                    f"get_category_article_count_service: {data_source} 数据已更新缓存，总耗时 {total_time:.3f}s"
                )
            except Exception as cache_e:
                Logger.warning(f"更新缓存失败: {cache_e}")

        if ch_conn:
            self.articleMapper.return_clickhouse_connection(ch_conn)

        return result

    def get_monthly_publish_count_service(
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

        # ========== 步骤1: 尝试从缓存获取 ==========
        try:
            ch_conn = self.articleMapper.get_clickhouse_connection()
            cached_result = self._publish_time_cache.get(ch_conn)
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

        # 1.优先 ClickHouse
        try:
            publish_data = (
                self.articleMapper.get_monthly_publish_count_clickhouse_mapper()
            )
            data_source = "ClickHouse"
            Logger.info(Constants.MONTHLY_STATISTICS_CLICKHOUSE_GET)
        except Exception as ch_e:
            Logger.warning(
                f"get_monthly_publish_count_service: ClickHouse 查询失败，降级为 DB: {ch_e}"
            )

        # 2.DB 兜底
        if not publish_data or len(publish_data) == 0:
            publish_data = self.articleMapper.get_monthly_publish_count_db_mapper(db)
            data_source = "DB"
            Logger.info(Constants.MONTHLY_STATISTICS_DB_SOURCE)

        # ========== 步骤3: 补充缺失月份，置为0 ==========
        # 获取当前日期所在的月份
        now = datetime.now()

        # 构建最近6个月的月份列表（从当前月向前推）
        expected_months = []
        for i in range(5, -1, -1):  # 从5个月前到当前月
            month_date = now - relativedelta(months=i)
            expected_months.append(month_date.strftime("%Y-%m"))

        # 创建数据字典，便于查找
        data_dict = {item["year_month"]: item["count"] for item in publish_data}

        # 补充缺失月份
        result = []
        for month in expected_months:
            result.append({"year_month": month, "count": data_dict.get(month, 0)})

        # ========== 步骤4: 按月份从远到近排序 ==========
        result.sort(key=lambda x: x["year_month"], reverse=False)

        Logger.info(
            f"get_monthly_publish_count_service: 获取过去6个月中 {len(result)} 个月份数据，有文章的月份数: {len([r for r in result if r['count'] > 0])}"
        )

        # ========== 步骤5: 更新缓存 ==========
        if ch_conn and result:
            try:
                self._publish_time_cache.set(result, ch_conn)
                total_time = time.time() - start
                Logger.info(
                    f"get_monthly_publish_count_service: {data_source} 数据已更新缓存，总耗时 {total_time:.3f}s"
                )
            except Exception as cache_e:
                Logger.warning(f"更新缓存失败: {cache_e}")

        if ch_conn:
            self.articleMapper.return_clickhouse_connection(ch_conn)

        return result


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
