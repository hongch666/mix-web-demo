from functools import lru_cache
from typing import Dict, Any
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlmodel import Session
from fastapi import Depends
from api.mapper import (
    FocusMapper, get_focus_mapper, 
    LikeMapper, get_like_mapper, 
    CollectMapper, get_collect_mapper, 
    ArticleMapper, get_article_mapper, 
    CommentsMapper, get_comments_mapper, 
    ArticleLogMapper, get_articlelog_mapper
)
from common.utils import fileLogger as logger

class UserService:
    def __init__(
        self, 
            focusMapper: FocusMapper = None, 
            likeMapper: LikeMapper = None, 
            collectMapper: CollectMapper = None, 
            articleMapper: ArticleMapper = None, 
            commentsMapper: CommentsMapper = None, 
            articleLogMapper: ArticleLogMapper = None
        ):
        self.focusMapper = focusMapper
        self.likeMapper = likeMapper
        self.collectMapper = collectMapper
        self.articleMapper = articleMapper
        self.commentsMapper = commentsMapper
        self.articleLogMapper = articleLogMapper

    def get_new_followers_service(self, db: Session, user_id: int, period: str = "day") -> Dict[str, Any]:
        """
        获取新增粉丝数统计
        period: "day" 前7天, "month" 前6个月, "year" 前3年
        """
        try:
            timeline = []
            
            if period == "day":
                # 前7天
                for i in range(6, -1, -1):
                    date = datetime.now() - timedelta(days=i)
                    start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
                    count = self.focusMapper.get_followers_in_period_mapper(db, user_id, start_date, end_date)
                    timeline.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "count": count
                    })
            elif period == "month":
                # 前6个月
                for i in range(5, -1, -1):
                    date = datetime.now() - relativedelta(months=i)
                    start_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    if date.month == 12:
                        end_date = (date.replace(day=1) + relativedelta(months=1)).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
                    else:
                        end_date = (date.replace(day=1) + relativedelta(months=1)).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
                    count = self.focusMapper.get_followers_in_period_mapper(db, user_id, start_date, end_date)
                    timeline.append({
                        "month": date.strftime("%Y-%m"),
                        "count": count
                    })
            elif period == "year":
                # 前3年
                for i in range(2, -1, -1):
                    date = datetime.now() - relativedelta(years=i)
                    start_date = date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                    end_date = date.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
                    count = self.focusMapper.get_followers_in_period_mapper(db, user_id, start_date, end_date)
                    timeline.append({
                        "year": date.strftime("%Y"),
                        "count": count
                    })
            
            return {
                "period": period,
                "timeline": timeline
            }
        except Exception as e:
            logger.error(f"获取新增粉丝数统计失败: {e}")
            return {"period": period, "timeline": []}

    def get_article_view_distribution_service(self, user_id: int) -> Dict[str, Any]:
        """获取用户的文章浏览分布"""
        try:
            result = self.articleLogMapper.get_user_view_distribution_mapper(user_id)
            return result
        except Exception as e:
            logger.error(f"获取文章浏览分布失败: {e}", exc_info=True)
            return {"total_views": 0, "articles": []}

    def get_author_follow_statistics_service(self, db: Session, user_id: int) -> Dict[str, Any]:
        """获取用户关注作者的统计"""
        try:
            # 总关注作者数
            total_authors = self.focusMapper.get_total_follows_mapper(db, user_id)
            
            # 前7天每天关注的作者数
            daily_follows = []
            for i in range(6, -1, -1):
                date = datetime.now() - timedelta(days=i)
                start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                count = 0
                results = self.focusMapper.get_daily_follows_mapper(db, user_id, start_date, end_date)
                if results and len(results) > 0:
                    count = results[0][1]  # 获取count
                
                daily_follows.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "count": count
                })
            
            return {
                "total_authors": total_authors,
                "daily_follows": daily_follows
            }
        except Exception as e:
            logger.error(f"获取关注作者统计失败: {e}")
            return {"total_authors": 0, "daily_follows": []}

    def get_monthly_comment_trend_service(self, db: Session, user_id: int) -> Dict[str, Any]:
        """获取用户本月评论的趋势"""
        try:
            return self.commentsMapper.get_monthly_comment_trend_mapper(db, user_id)
        except Exception as e:
            logger.error(f"获取评论趋势失败: {e}")
            return {"total": 0, "daily_trends": []}

    def get_monthly_like_trend_service(self, db: Session, user_id: int) -> Dict[str, Any]:
        """获取用户本月点赞的趋势"""
        try:
            return self.likeMapper.get_monthly_like_trend_mapper(db, user_id)
        except Exception as e:
            logger.error(f"获取点赞趋势失败: {e}")
            return {"total": 0, "daily_trends": []}

    def get_monthly_collect_trend_service(self, db: Session, user_id: int) -> Dict[str, Any]:
        """获取用户本月收藏的趋势"""
        try:
            return self.collectMapper.get_monthly_collect_trend_mapper(db, user_id)
        except Exception as e:
            logger.error(f"获取收藏趋势失败: {e}")
            return {"total": 0, "daily_trends": []}


@lru_cache()
def get_user_service(
        focusMapper: FocusMapper = Depends(get_focus_mapper), 
        likeMapper: LikeMapper = Depends(get_like_mapper), 
        collectMapper: CollectMapper = Depends(get_collect_mapper), 
        articleMapper: ArticleMapper = Depends(get_article_mapper), 
        commentsMapper: CommentsMapper = Depends(get_comments_mapper), 
        articleLogMapper: ArticleLogMapper = Depends(get_articlelog_mapper)
    ) -> UserService:
    """获取 UserService 单例实例"""
    return UserService(
            focusMapper, 
            likeMapper, 
            collectMapper, 
            articleMapper, 
            commentsMapper, 
            articleLogMapper
        )
