from functools import lru_cache
from datetime import datetime
from typing import Any, Dict, List
from sqlmodel import Session, select, func, cast, Date
from entity.po import Focus
from common.utils import fileLogger as logger

class FocusMapper:
    """关注 Mapper"""
    
    def get_total_followers_mapper(self, db: Session, user_id: int) -> int:
        """获取用户的粉丝总数（被多少人关注）"""
        
        statement = select(func.count(Focus.id)).where(Focus.focus_id == user_id)
        total_followers = db.exec(statement).first()
        return total_followers if total_followers else 0

    def get_followers_in_period_mapper(self, db: Session, user_id: int, start_date: datetime, end_date: datetime) -> int:
        """获取指定时间段内的新增粉丝数"""

        statement = select(func.count(Focus.id)).where(
            Focus.focus_id == user_id,
            Focus.created_time >= start_date,
            Focus.created_time <= end_date
        )
        count = db.exec(statement).first()
        return count if count else 0

    def get_daily_followers_mapper(self, db: Session, user_id: int, start_date: datetime, end_date: datetime) -> List[Any]:
        """获取指定时间段内每天的新增粉丝数"""

        statement = select(
            cast(Focus.created_time, Date).label("date"),
            func.count(Focus.id).label("count")
        ).where(
            Focus.focus_id == user_id,
            Focus.created_time >= start_date,
            Focus.created_time <= end_date
        ).group_by(cast(Focus.created_time, Date)).order_by(cast(Focus.created_time, Date))
        
        results = db.exec(statement).all()
        return results if results else []

    def get_total_follows_mapper(self, db: Session, user_id: int) -> int:
        """获取用户的总关注数"""

        statement = select(func.count(Focus.id)).where(Focus.user_id == user_id)
        total_follows = db.exec(statement).first()
        return total_follows if total_follows else 0

    def get_daily_follows_mapper(self, db: Session, user_id: int, start_date: datetime, end_date: datetime) -> List[Any]:
        """获取指定时间段内每天的关注数"""

        statement = select(
            cast(Focus.created_time, Date).label("date"),
            func.count(Focus.id).label("count")
        ).where(
            Focus.user_id == user_id,
            Focus.created_time >= start_date,
            Focus.created_time <= end_date
        ).group_by(cast(Focus.created_time, Date)).order_by(cast(Focus.created_time, Date))
        
        results = db.exec(statement).all()
        return results if results else []

    def get_monthly_follow_trend_mapper(self, db: Session, user_id: int) -> Dict[str, Any]:
        """获取用户本月关注的趋势"""

        today = datetime.now()
        first_day = datetime(today.year, today.month, 1)
        if today.month == 12:
            last_day = datetime(today.year + 1, 1, 1).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            last_day = datetime(today.year, today.month + 1, 1).replace(hour=0, minute=0, second=0, microsecond=0)
        
        statement = select(
            cast(Focus.created_time, Date).label("date"),
            func.count(Focus.id).label("count")
        ).where(
            Focus.user_id == user_id,
            Focus.created_time >= first_day,
            Focus.created_time < last_day
        ).group_by(cast(Focus.created_time, Date)).order_by(cast(Focus.created_time, Date))
        
        results = db.exec(statement).all()
        
        daily_trends: List[Dict[str, Any]] = []
        total: int = 0
        for row in results:
            date_str = str(row[0])
            count = row[1]
            daily_trends.append({
                "date": date_str,
                "count": count
            })
            total += count
        
        logger.debug(f"用户 {user_id} 本月关注趋势: 总数={total}, 天数={len(daily_trends)}")
        return {
            "total": total,
            "daily_trends": daily_trends
        }

    def get_monthly_follower_trend_mapper(self, db: Session, user_id: int) -> Dict[str, Any]:
        """获取用户本月新增粉丝的趋势"""

        today = datetime.now()
        first_day = datetime(today.year, today.month, 1)
        if today.month == 12:
            last_day = datetime(today.year + 1, 1, 1).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            last_day = datetime(today.year, today.month + 1, 1).replace(hour=0, minute=0, second=0, microsecond=0)
        
        statement = select(
            cast(Focus.created_time, Date).label("date"),
            func.count(Focus.id).label("count")
        ).where(
            Focus.focus_id == user_id,
            Focus.created_time >= first_day,
            Focus.created_time < last_day
        ).group_by(cast(Focus.created_time, Date)).order_by(cast(Focus.created_time, Date))
        
        results = db.exec(statement).all()
        
        daily_trends: List[Dict[str, Any]] = []
        total: int = 0
        for row in results:
            date_str = str(row[0])
            count = row[1]
            daily_trends.append({
                "date": date_str,
                "count": count
            })
            total += count
        
        logger.debug(f"用户 {user_id} 本月粉丝趋势: 总数={total}, 天数={len(daily_trends)}")
        return {
            "total": total,
            "daily_trends": daily_trends
        }


@lru_cache()
def get_focus_mapper() -> FocusMapper:
    """获取 FocusMapper 单例实例"""
    return FocusMapper()
