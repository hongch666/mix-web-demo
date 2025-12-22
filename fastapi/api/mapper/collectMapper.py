from functools import lru_cache
from sqlmodel import Session, select, func
from entity.po import Collect
from common.utils import fileLogger as logger
from . import get_article_mapper


class CollectMapper:
    
    def get_total_collects_mapper(self, db: Session) -> int:
        """获取所有文章的总收藏数"""
        try:
            statement = select(func.count(Collect.id))
            total_collects = db.exec(statement).first()
            return total_collects if total_collects else 0
        except Exception as e:
            logger.warning(f"获取总收藏数失败，返回0: {e}")
            return 0

    def get_average_collects_mapper(self, db: Session) -> float:
        """获取每篇文章的平均收藏数"""
        try:
            
            article_mapper = get_article_mapper()
            total_articles = article_mapper.get_total_articles_mapper(db)
            if total_articles == 0:
                return 0
            total_collects = self.get_total_collects_mapper(db)
            return round(total_collects / total_articles, 2)
        except Exception as e:
            logger.warning(f"获取平均收藏数失败，返回0: {e}")
            return 0


@lru_cache()
def get_collect_mapper() -> CollectMapper:
    """获取 CollectMapper 单例实例"""
    return CollectMapper()