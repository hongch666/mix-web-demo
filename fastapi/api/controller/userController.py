from fastapi import APIRouter, Depends, Request
from sqlmodel import Session
from starlette.concurrency import run_in_threadpool
from typing import Any, Dict
from api.service import UserService, get_user_service
from config import get_db
from common.utils import success
from common.decorators import log

router: APIRouter = APIRouter(
    prefix="/analyze/user",
    tags=["用户个人数据分析"],
)

@router.get(
    "/new-followers",
    summary="获取新增粉丝数统计",
    description="获取指定周期内的新增粉丝数（支持按日/月/年统计）"
)
@log("获取新增粉丝数统计")
async def get_new_followers(
    request: Request,
    user_id: int,
    period: str = "day",
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service)
) -> Any:
    """
    获取新增粉丝数统计
    - period: day (前7天), month (前12个月), year (前3年)
    """
    result: Dict[str, Any] = await run_in_threadpool(service.get_new_followers_service, db, user_id, period)
    return success(result)

@router.get(
    "/article-view-distribution",
    summary="获取文章浏览分布",
    description="查询用户浏览过的文章及其浏览次数分布"
)
@log("获取文章浏览分布")
async def get_article_view_distribution(
    request: Request,
    user_id: int,
    service: UserService = Depends(get_user_service)
) -> Any:
    """
    获取文章浏览分布
    返回: 浏览总数和各文章的浏览次数（按浏览量从高到低排序）
    """
    result: Dict[str, Any] = await run_in_threadpool(service.get_article_view_distribution_service, user_id)
    return success(result)

@router.get(
    "/author-follow-statistics",
    summary="获取关注作者统计",
    description="获取用户的总关注数和前7天每天关注的作者数"
)
@log("获取关注作者统计")
async def get_author_follow_statistics(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service)
) -> Any:
    """
    获取关注作者统计
    返回: 总关注作者数和前7天每天关注的作者数
    """
    result: Dict[str, Any] = await run_in_threadpool(service.get_author_follow_statistics_service, db, user_id)
    return success(result)

@router.get(
    "/monthly-comment-trend",
    summary="获取本月评论趋势",
    description="按天统计用户本月的评论数量趋势"
)
@log("获取本月评论趋势")
async def get_monthly_comment_trend(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service)
) -> Any:
    """
    获取本月评论趋势
    返回: 本月总评论数和每日评论数
    """
    result: Dict[str, Any] = await run_in_threadpool(service.get_monthly_comment_trend_service, db, user_id)
    return success(result)

@router.get(
    "/monthly-like-trend",
    summary="获取本月点赞趋势",
    description="按天统计用户本月的点赞数量趋势"
)
@log("获取本月点赞趋势")
async def get_monthly_like_trend(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service)
) -> Any:
    """
    获取本月点赞趋势
    返回: 本月总点赞数和每日点赞数
    """
    result: Dict[str, Any] = await run_in_threadpool(service.get_monthly_like_trend_service, db, user_id)
    return success(result)

@router.get(
    "/monthly-collect-trend",
    summary="获取本月收藏趋势",
    description="按天统计用户本月的收藏数量趋势"
)
@log("获取本月收藏趋势")
async def get_monthly_collect_trend(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service)
) -> Any:
    """
    获取本月收藏趋势
    返回: 本月总收藏数和每日收藏数
    """
    result: Dict[str, Any] = await run_in_threadpool(service.get_monthly_collect_trend_service, db, user_id)
    return success(result)
