from fastapi import APIRouter, Depends, Request
from sqlmodel import Session
from starlette.concurrency import run_in_threadpool
from typing import Any, Dict
from api.service import UserService, get_user_service
from common.config import get_db
from common.utils import success
from common.decorators import log

router: APIRouter = APIRouter(
    prefix="/analyze/user",
    tags=["用户个人数据分析接口"],
)

@router.get(
    "/new-followers",
    summary="获取新增粉丝数统计",
    description="获取指定周期内的新增粉丝数（支持按日/月/年统计）"
)
@log("获取新增粉丝数统计")
async def get_new_followers(
    _: Request,
    user_id: int,
    period: str = "day",
    db: Session = Depends(get_db),
    userService: UserService = Depends(get_user_service)
) -> Any:
    """获取新增粉丝数统计"""
    
    result: Dict[str, Any] = await run_in_threadpool(userService.get_new_followers_service, db, user_id, period)
    return success(result)

@router.get(
    "/article-view-distribution",
    summary="获取文章浏览分布",
    description="查询用户浏览过的文章及其浏览次数分布"
)
@log("获取文章浏览分布")
async def get_article_view_distribution(
    _: Request,
    user_id: int,
    userService: UserService = Depends(get_user_service)
) -> Any:
    """获取文章浏览分布"""
    
    result: Dict[str, Any] = await run_in_threadpool(userService.get_article_view_distribution_service, user_id)
    return success(result)

@router.get(
    "/author-follow-statistics",
    summary="获取关注作者统计",
    description="获取用户的总关注数和前7天每天关注的作者数"
)
@log("获取关注作者统计")
async def get_author_follow_statistics(
    _: Request,
    user_id: int,
    db: Session = Depends(get_db),
    userService: UserService = Depends(get_user_service)
) -> Any:
    """获取关注作者统计"""
    
    result: Dict[str, Any] = await run_in_threadpool(userService.get_author_follow_statistics_service, db, user_id)
    return success(result)

@router.get(
    "/monthly-comment-trend",
    summary="获取本月评论趋势",
    description="按天统计用户本月的评论数量趋势"
)
@log("获取本月评论趋势")
async def get_monthly_comment_trend(
    _: Request,
    user_id: int,
    db: Session = Depends(get_db),
    userService: UserService = Depends(get_user_service)
) -> Any:
    """获取本月评论趋势"""
    
    result: Dict[str, Any] = await run_in_threadpool(userService.get_monthly_comment_trend_service, db, user_id)
    return success(result)

@router.get(
    "/monthly-like-trend",
    summary="获取本月点赞趋势",
    description="按天统计用户本月的点赞数量趋势"
)
@log("获取本月点赞趋势")
async def get_monthly_like_trend(
    _: Request,
    user_id: int,
    db: Session = Depends(get_db),
    userService: UserService = Depends(get_user_service)
) -> Any:
    """获取本月点赞趋势"""
    
    result: Dict[str, Any] = await run_in_threadpool(userService.get_monthly_like_trend_service, db, user_id)
    return success(result)

@router.get(
    "/monthly-collect-trend",
    summary="获取本月收藏趋势",
    description="按天统计用户本月的收藏数量趋势"
)
@log("获取本月收藏趋势")
async def get_monthly_collect_trend(
    _: Request,
    user_id: int,
    db: Session = Depends(get_db),
    userService: UserService = Depends(get_user_service)
) -> Any:
    """获取本月收藏趋势"""
    
    result: Dict[str, Any] = await run_in_threadpool(userService.get_monthly_collect_trend_service, db, user_id)
    return success(result)
