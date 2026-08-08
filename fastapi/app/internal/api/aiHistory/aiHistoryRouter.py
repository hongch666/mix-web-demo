from typing import Any

from app.common.decorators import log, requireInternalToken
from app.core.base import ApiResponse, success
from app.dependencies import AiHistoryServiceDep, DbSession
from app.internal.schemas import CreateHistoryDTO

from fastapi import APIRouter, Path, Query, Request

router: APIRouter = APIRouter(
    prefix="/ai_history",
    tags=["AI历史模块"],
)


@router.post(
    "",
    summary="创建AI历史记录",
    description="创建一条AI历史记录",
    response_model=ApiResponse,
)
@requireInternalToken
@log("创建AI历史记录")
async def create_ai_history(
    request: Request,
    data: CreateHistoryDTO,
    db: DbSession,
    ai_history_service: AiHistoryServiceDep,
) -> ApiResponse:
    """创建AI历史记录接口"""

    await ai_history_service.create_ai_history(data, db)
    return success()


@router.get(
    "/list",
    summary="获取所有AI历史记录",
    description="获取指定用户的所有AI历史记录",
    response_model=ApiResponse,
)
@log("获取所有AI历史记录")
async def get_all_ai_history(
    request: Request,
    db: DbSession,
    ai_history_service: AiHistoryServiceDep,
    userId: int = Query(alias="user_id"),
) -> ApiResponse:
    """获取所有AI历史记录接口"""

    histories: list[dict[str, Any]] = await ai_history_service.get_all_ai_history(
        userId, db
    )
    return success(data=histories)


@router.delete(
    "/{user_id}",
    summary="删除用户所有AI历史记录",
    description="删除指定用户的所有AI历史记录",
    response_model=ApiResponse,
)
@log("删除用户所有AI历史记录")
async def delete_ai_history(
    request: Request,
    db: DbSession,
    ai_history_service: AiHistoryServiceDep,
    userId: int = Path(alias="user_id"),
) -> ApiResponse:
    """删除用户所有AI历史记录接口"""

    await ai_history_service.delete_ai_history_by_userid(userId, db)
    return success()
