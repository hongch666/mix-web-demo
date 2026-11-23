from typing import Optional

from pydantic import BaseModel, Field


class ArticleStatisticsResponse(BaseModel):
    """平台文章统计响应，包含阅读、文章、点赞、收藏等汇总指标"""

    total_views: int = Field(description="总阅读量")
    total_articles: int = Field(description="文章总数")
    active_authors: int = Field(description="活跃作者数")
    average_views: float = Field(description="文章平均阅读量")
    total_likes: int = Field(description="总点赞数")
    average_likes: float = Field(description="文章平均点赞数")
    total_collects: int = Field(description="总收藏数")
    average_collects: float = Field(description="文章平均收藏数")


class CategoryArticleCountResponse(BaseModel):
    """单个分类文章数量统计项的响应模型"""

    category_id: int = Field(description="分类 ID")
    category_name: str = Field(description="分类名称")
    article_count: int = Field(description="文章数量")


class MonthlyPublishCountResponse(BaseModel):
    """单个月份文章发布数量的响应模型"""

    year_month: str = Field(description="月份，格式为 YYYY-MM")
    count: int = Field(description="发布数量")


class ArticleTop10Response(BaseModel):
    """文章阅读量前十榜单响应项"""

    id: int = Field(description="文章 ID")
    title: str = Field(description="文章标题")
    user_id: int = Field(description="作者用户 ID")
    username: Optional[str] = Field(default=None, description="作者用户名")
    views: int = Field(description="文章阅读量")
    likes: Optional[int] = Field(default=None, description="文章点赞数")
    collects: Optional[int] = Field(default=None, description="文章收藏数")
    create_at: Optional[str] = Field(default=None, description="创建时间")
    update_at: Optional[str] = Field(default=None, description="更新时间")
