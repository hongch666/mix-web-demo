from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from .algorithmDTO import ScoreWeightItem, ScriptParamItem


class EmptyResponseData(BaseModel):
    """无业务数据的成功响应"""


class AiHistoryResponse(BaseModel):
    """AI 历史记录"""

    id: int = Field(description="记录 ID")
    user_id: int = Field(description="用户 ID")
    ask: str = Field(description="用户提问")
    reply: str = Field(description="模型回复")
    thinking: Optional[str] = Field(default=None, description="模型思考过程")
    ai_type: str = Field(description="AI 服务类型")
    created_at: Optional[str] = Field(default=None, description="创建时间")
    updated_at: Optional[str] = Field(default=None, description="更新时间")


class DeletedResponse(BaseModel):
    deleted: bool = Field(description="是否删除成功")


class ArticleStatisticsResponse(BaseModel):
    total_views: int = Field(description="总阅读量")
    total_articles: int = Field(description="文章总数")
    active_authors: int = Field(description="活跃作者数")
    average_views: float = Field(description="文章平均阅读量")
    total_likes: int = Field(description="总点赞数")
    average_likes: float = Field(description="文章平均点赞数")
    total_collects: int = Field(description="总收藏数")
    average_collects: float = Field(description="文章平均收藏数")


class CategoryArticleCountResponse(BaseModel):
    category_id: int = Field(description="分类 ID")
    category_name: str = Field(description="分类名称")
    article_count: int = Field(description="文章数量")


class MonthlyPublishCountResponse(BaseModel):
    year_month: str = Field(description="月份，格式为 YYYY-MM")
    count: int = Field(description="发布数量")


class UserTimelineItem(BaseModel):
    date: Optional[str] = Field(default=None, description="日期")
    month: Optional[str] = Field(default=None, description="月份")
    year: Optional[str] = Field(default=None, description="年份")
    count: int = Field(description="统计数量")


class UserFollowerResponse(BaseModel):
    period: str = Field(description="统计周期")
    timeline: list[UserTimelineItem] = Field(description="周期统计")


class ArticleViewDistributionResponse(BaseModel):
    total_views: int = Field(description="总阅读量")
    articles: list[dict[str, Any]] = Field(description="文章阅读分布")


class AuthorFollowStatisticsResponse(BaseModel):
    total_authors: int = Field(description="关注作者总数")
    daily_follows: list[UserTimelineItem] = Field(description="每日关注统计")


class ActionTrendResponse(BaseModel):
    total: int = Field(description="总数量")
    daily_trends: list[UserTimelineItem] = Field(description="每日趋势")


class UserProfileResponse(BaseModel):
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


class ApiLogAverageResponse(BaseModel):
    api_path: str = Field(description="API 路径")
    api_method: str = Field(description="请求方法")
    api_description: str = Field(description="API 描述")
    avg_response_time: float = Field(description="平均响应时间")
    call_count: int = Field(description="调用次数")


class ApiLogCalledCountResponse(BaseModel):
    api_path: str = Field(description="API 路径")
    api_method: str = Field(description="请求方法")
    api_description: str = Field(description="API 描述")
    call_count: int = Field(description="调用次数")
    avg_response_time: float = Field(description="平均响应时间")


class GenerateCommentTaskResponse(BaseModel):
    message: str = Field(description="任务提交消息")
    article_id: int = Field(description="文章 ID")


class SearchWeightsResponse(BaseModel):
    weights: list[ScoreWeightItem] = Field(description="搜索权重列表")


class SearchScriptResponseData(BaseModel):
    es_script: str = Field(description="ES 搜索脚本")


class ScriptParamsResponse(BaseModel):
    script_params: list[ScriptParamItem] = Field(description="脚本参数映射")
