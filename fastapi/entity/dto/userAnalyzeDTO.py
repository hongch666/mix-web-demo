from sqlmodel import SQLModel
from typing import List, Dict, Any

class NewFollowersDTO(SQLModel):
    """新增粉丝数统计 DTO"""
    period: str  # "day" / "month" / "year"
    timeline: List[Dict[str, Any]]  # [{"date": "2024-01-01", "count": 5}, ...]

class ArticleViewDistributionDTO(SQLModel):
    """文章浏览分布 DTO"""
    total_views: int  # 浏览总数
    articles: List[Dict[str, Any]]  # [{"article_id": 1, "article_title": "...", "views": 100}, ...]

class AuthorFollowStatisticsDTO(SQLModel):
    """关注作者统计 DTO"""
    total_authors: int  # 总关注作者数
    daily_follows: List[Dict[str, Any]]  # [{"date": "2024-01-01", "count": 2}, ...]

class DailyTrendDTO(SQLModel):
    """按天的趋势数据 DTO"""
    date: str
    count: int

class MonthlyTrendDTO(SQLModel):
    """月度趋势统计 DTO"""
    total: int
    daily_trends: List[DailyTrendDTO]
