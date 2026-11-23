from typing import Optional

from pydantic import BaseModel, Field


class UserTimelineItem(BaseModel):
    """用户分析时间线中单个时间点与数量的响应项"""

    date: Optional[str] = Field(default=None, description="日期")
    month: Optional[str] = Field(default=None, description="月份")
    year: Optional[str] = Field(default=None, description="年份")
    count: int = Field(description="统计数量")


class UserFollowerResponse(BaseModel):
    """按统计周期返回的用户关注时间线响应"""

    period: str = Field(description="统计周期")
    timeline: list[UserTimelineItem] = Field(description="周期统计")


class ArticleViewItem(BaseModel):
    """单篇文章阅读分布响应项"""

    article_id: int = Field(description="文章 ID")
    title: Optional[str] = Field(default=None, description="文章标题")
    views: int = Field(description="文章阅读量")


class ArticleViewDistributionResponse(BaseModel):
    """用户文章阅读分布响应，含总阅读量与各文章明细"""

    total_views: int = Field(description="总阅读量")
    articles: list[ArticleViewItem] = Field(description="文章阅读分布")


class AuthorFollowStatisticsResponse(BaseModel):
    """用户关注作者统计响应，含关注总数与每日关注明细"""

    total_authors: int = Field(description="关注作者总数")
    daily_follows: list[UserTimelineItem] = Field(description="每日关注统计")


class ActionTrendResponse(BaseModel):
    """用户行为趋势响应，含总量与每日趋势明细"""

    total: int = Field(description="总数量")
    daily_trends: list[UserTimelineItem] = Field(description="每日趋势")


class UserProfileResponse(BaseModel):
    """用户画像统计响应，包含发文、获赞、粉丝等全量指标"""

    user_id: int = Field(description="用户 ID")
    user_name: str = Field(description="用户名")
    total_articles: int = Field(description="发布文章数")
    total_views_received: int = Field(description="文章获阅读数")
    total_likes_received: int = Field(description="文章获点赞数")
    total_collects_received: int = Field(description="文章获收藏数")
    total_followers: int = Field(description="粉丝数")
    total_likes_given: int = Field(description="点赞数")
    total_collects_given: int = Field(description="收藏数")
    total_comments: int = Field(description="评论数")
    total_focus: int = Field(description="关注数")
    last_active_time: Optional[str] = Field(default=None, description="最后活跃时间")
