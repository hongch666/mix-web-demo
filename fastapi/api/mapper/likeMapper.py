from functools import lru_cache
from sqlmodel import Session, select, func
from entity.po import Like
from common.utils import fileLogger as logger
from datetime import datetime
from sqlalchemy import cast, Date
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

    def get_monthly_like_trend_mapper(self, db: Session, user_id: int) -> dict:
        """获取用户本月点赞的趋势"""
        try:
            today = datetime.now()
            first_day = datetime(today.year, today.month, 1)
            if today.month == 12:
                last_day = datetime(today.year + 1, 1, 1).replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                last_day = datetime(today.year, today.month + 1, 1).replace(hour=0, minute=0, second=0, microsecond=0)
            
            statement = select(
                cast(Like.created_time, Date).label("date"),
                func.count(Like.id).label("count")
            ).where(
                Like.user_id == user_id,
                Like.created_time >= first_day,
                Like.created_time < last_day
            ).group_by(cast(Like.created_time, Date)).order_by(cast(Like.created_time, Date))
            
            results = db.exec(statement).all()
            
            daily_trends = []
            total = 0
            for row in results:
                date_str = str(row[0])
                count = row[1]
                daily_trends.append({
                    "date": date_str,
                    "count": count
                })
                total += count
            
            logger.debug(f"用户 {user_id} 本月点赞趋势: 总数={total}, 天数={len(daily_trends)}")
            return {
                "total": total,
                "daily_trends": daily_trends
            }
        except Exception as e:
            logger.error(f"获取点赞趋势失败: {e}", exc_info=True)
            return {"total": 0, "daily_trends": []}


@lru_cache()
def get_like_mapper() -> LikeMapper:
    """获取 LikeMapper 单例实例"""
    return LikeMapper()