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


class ArticleViewDistributionResponse(BaseModel):
    """用户文章阅读分布响应，含总阅读量与各文章明细"""

    total_views: int = Field(description="总阅读量")
    articles: list[dict[str, Any]] = Field(description="文章阅读分布")


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


class ApiLogAverageResponse(BaseModel):
    """单个接口平均响应时间与调用次数的响应模型"""

    api_path: str = Field(description="API 路径")
    api_method: str = Field(description="请求方法")
    api_description: str = Field(description="API 描述")
    avg_response_time: float = Field(description="平均响应时间")
    call_count: int = Field(description="调用次数")


class ApiLogCalledCountResponse(BaseModel):
    """单个接口调用次数与平均响应时间的响应模型"""

    api_path: str = Field(description="API 路径")
    api_method: str = Field(description="请求方法")
    api_description: str = Field(description="API 描述")
    call_count: int = Field(description="调用次数")
    avg_response_time: float = Field(description="平均响应时间")


class GenerateCommentTaskResponse(BaseModel):
    """AI 评论生成任务提交结果的响应模型"""

    message: str = Field(description="任务提交消息")
    article_id: int = Field(description="文章 ID")


class SearchWeightsResponse(BaseModel):
    """搜索权重列表的响应模型"""

    weights: list[ScoreWeightItem] = Field(description="搜索权重列表")


class SearchScriptResponseData(BaseModel):
    """返回 ES 搜索脚本的响应数据模型"""

    es_script: str = Field(description="ES 搜索脚本")


class ScriptParamsResponse(BaseModel):
    """返回搜索脚本参数映射的响应模型"""

    script_params: list[ScriptParamItem] = Field(description="脚本参数映射")
