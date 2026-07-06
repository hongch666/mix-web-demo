from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Any, Dict, List

from app.core.base import Constants, HttpCode, Logger
from app.core.db import async_db as mongo_db
from app.core.db import get_db
from app.core.errors import BusinessException
from sqlalchemy.ext.asyncio import AsyncSession

from .article import ArticleMapper, get_article_mapper


class ArticleLogMapper:
    """文章日志 Mapper"""

    async def get_search_keywords_articlelog_mapper(self) -> List[str]:
        logs: Any = mongo_db["articlelogs"]
        pipeline = [
            {"$match": {"action": "search"}},
            {"$project": {"keyword": "$content.Keyword"}},
            {"$match": {"keyword": {"$ne": "", "$exists": True}}},
            {"$group": {"_id": "$keyword"}},
            {"$sort": {"_id": 1}},
        ]
        cursor: Any = logs.aggregate(pipeline)
        results: List[Dict[str, Any]] = await cursor.to_list(length=None)
        all_keywords: List[str] = [doc["_id"] for doc in results]
        return all_keywords

    async def get_user_view_distribution_mapper(self, user_id: int) -> Dict[str, Any]:
        """获取用户的文章浏览分布"""
        try:
            logs: Any = mongo_db["articlelogs"]
            Logger.debug(f"开始查询用户 {user_id} 的浏览分布")

            # 使用 aggregation pipeline 进行数据处理
            pipeline = [
                {"$match": {"userId": user_id, "action": "view"}},
                {"$group": {"_id": "$articleId", "views": {"$sum": 1}}},
                {"$match": {"_id": {"$ne": None}}},
                {"$sort": {"views": -1}},
            ]

            cursor: Any = logs.aggregate(pipeline)
            results: List[Dict[str, Any]] = await cursor.to_list(length=None)

            if not results:
                Logger.info(f"用户 {user_id} 无浏览记录")
                return {"total_views": 0, "articles": []}

            # 提取所有文章ID进行批量查询
            article_ids: List[int] = [doc["_id"] for doc in results]
            article_mapper: ArticleMapper = get_article_mapper()

            # 批量获取所有文章信息（只需一次查询）
            db_generator: AsyncGenerator[AsyncSession, None] = get_db()
            db: AsyncSession = await anext(db_generator)
            try:
                articles_dict: Dict[
                    int, Any
                ] = await article_mapper.get_articles_by_ids_mapper_async(
                    article_ids, db
                )
            finally:
                await db_generator.aclose()

            # 处理聚合结果并匹配文章标题
            articles = []
            total_views = 0

            for doc in results:
                article_id = doc["_id"]
                views = doc["views"]
                total_views += views

                article = articles_dict.get(article_id)
                title = article.title if article else Constants.UNKNOWN_ARTICLE
                articles.append(
                    {"article_id": article_id, "title": title, "views": views}
                )

            Logger.info(
                f"用户 {user_id} 的文章浏览分布: 总浏览数={total_views}, 文章数={len(articles)}"
            )

            return {"total_views": total_views, "articles": articles}
        except Exception as e:
            Logger.error(f"获取文章浏览分布失败: {e}", exc_info=True)
            raise BusinessException(
                Constants.GET_TOP_FAIL,
                HttpCode.INTERNAL_SERVER_ERROR,
                Constants.ERROR_FASTAPI_SERVER_ERROR,
            )


@lru_cache()
def get_articlelog_mapper() -> ArticleLogMapper:
    return ArticleLogMapper()
