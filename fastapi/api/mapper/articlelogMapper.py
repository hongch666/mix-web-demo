from functools import lru_cache
from typing import Any, Dict, List
from config import db as mongo_db, get_db
from common.utils import fileLogger as logger
from api.mapper import get_article_mapper

class ArticleLogMapper:
    def get_search_keywords_articlelog_mapper(self) -> List[str]:
        logs = mongo_db["articlelogs"]
        cursor = logs.find({"action": "search"})
        all_keywords: List[str] = []
        for log in cursor:
            content: Dict[str, Any] = log.get('content', {})
            if 'Keyword' in content:
                if content['Keyword'] == "":
                    continue
                all_keywords.append(content['Keyword'])
        return all_keywords

    def get_user_view_distribution_mapper(self, user_id: int) -> Dict[str, Any]:
        """获取用户的文章浏览分布"""
        try:
            logs = mongo_db["articlelogs"]
            logger.debug(f"开始查询用户 {user_id} 的浏览分布")
            
            # 直接用find而不是聚合，更简单
            cursor = logs.find({"userId": user_id, "action": "view"})
            
            # 统计每篇文章的浏览次数
            article_views = {}
            total_views = 0
            
            for log in cursor:
                article_id: int = log.get('articleId', {})
                if article_id is not None:
                    article_views[article_id] = article_views.get(article_id, 0) + 1
                    total_views += 1
            
            # 获取article_mapper和db session
            article_mapper = get_article_mapper()
            db = get_db().__next__()
            
            # 按浏览次数从高到低排序，并获取文章标题
            articles = []
            for article_id, views in sorted(article_views.items(), key=lambda x: x[1], reverse=True):
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