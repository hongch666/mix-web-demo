from functools import lru_cache
from typing import Any, Dict, List
from config import db as mongo_db, get_db
from common.utils import fileLogger as logger
from api.mapper import get_article_mapper

class ArticleLogMapper:
    def get_search_keywords_articlelog_mapper(self) -> List[str]:
        logs = mongo_db["articlelogs"]
        pipeline = [
            {
                "$match": {"action": "search"}
            },
            {
                "$project": {"keyword": "$content.Keyword"}
            },
            {
                "$match": {
                    "keyword": {"$ne": "", "$exists": True}
                }
            },
            {
                "$group": {"_id": "$keyword"}
            },
            {
                "$sort": {"_id": 1}
            }
        ]
        cursor = logs.aggregate(pipeline)
        all_keywords: List[str] = [doc["_id"] for doc in cursor]
        return all_keywords

    def get_user_view_distribution_mapper(self, user_id: int) -> Dict[str, Any]:
        """获取用户的文章浏览分布"""
        try:
            logs = mongo_db["articlelogs"]
            logger.debug(f"开始查询用户 {user_id} 的浏览分布")
            
            # 使用 aggregation pipeline 进行数据处理
            pipeline = [
                {
                    "$match": {
                        "userId": user_id,
                        "action": "view"
                    }
                },
                {
                    "$group": {
                        "_id": "$articleId",
                        "views": {"$sum": 1}
                    }
                },
                {
                    "$match": {
                        "_id": {"$ne": None}
                    }
                },
                {
                    "$sort": {"views": -1}
                }
            ]
            
            cursor = logs.aggregate(pipeline)
            
            # 获取article_mapper和db session
            article_mapper = get_article_mapper()
            db = get_db().__next__()
            
            # 处理聚合结果并获取文章标题
            articles = []
            total_views = 0
            
            for doc in cursor:
                article_id = doc["_id"]
                views = doc["views"]
                total_views += views
                
                try:
                    article = article_mapper.get_article_by_id_mapper(article_id, db)
                    title = article.title if article else "未知文章"
                    articles.append({
                        "article_id": article_id,
                        "title": title,
                        "views": views
                    })
                except Exception as e:
                    logger.warning(f"获取文章 {article_id} 标题失败: {e}")
                    articles.append({
                        "article_id": article_id,
                        "title": "未知文章",
                        "views": views
                    })
            
            logger.info(f"用户 {user_id} 的文章浏览分布: 总浏览数={total_views}, 文章数={len(articles)}")
            
            return {
                "total_views": total_views,
                "articles": articles
            }
        except Exception as e:
            logger.error(f"获取文章浏览分布失败: {e}", exc_info=True)
            return {"total_views": 0, "articles": []}

@lru_cache()
def get_articlelog_mapper() -> ArticleLogMapper:
    return ArticleLogMapper()