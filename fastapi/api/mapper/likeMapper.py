from functools import lru_cache
from sqlmodel import Session, select, func
from entity.po import Like
from common.utils import fileLogger as logger
from . import get_article_mapper


class LikeMapper:
    
    def get_total_likes_mapper(self, db: Session) -> int:
        """获取所有文章的总点赞数"""
        try:
            statement = select(func.count(Like.id))
            total_likes = db.exec(statement).first()
            return total_likes if total_likes else 0
        except Exception as e:
            logger.warning(f"获取总点赞数失败，返回0: {e}")
            return 0

    def get_average_likes_mapper(self, db: Session) -> float:
        """获取每篇文章的平均点赞数"""
        try:
            article_mapper = get_article_mapper()
            total_articles = article_mapper.get_total_articles_mapper(db)
            if total_articles == 0:
                return 0
            total_likes = self.get_total_likes_mapper(db)
            return round(total_likes / total_articles, 2)
        except Exception as e:
            logger.warning(f"获取平均点赞数失败，返回0: {e}")
            return 0


@lru_cache()
def get_like_mapper() -> LikeMapper:
    """获取 LikeMapper 单例实例"""
    return LikeMapper()