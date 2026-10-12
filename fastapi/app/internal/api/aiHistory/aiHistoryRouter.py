from typing import Any

from fastapi import APIRouter, Path, Query, Request

from app.core.base import ApiResponse, success
from app.core.decorators import log, requireSelf
from app.dependencies import AiHistoryServiceDep, DbSession
from app.internal.schemas import AiHistoryResponse

router: APIRouter = APIRouter(
    prefix="/ai_history",
    tags=["AI历史模块"],
)


@router.get(
    "/list",
    summary="获取所有AI历史记录",
    description="获取指定用户的所有AI历史记录",
    response_model=ApiResponse[list[AiHistoryResponse]],
)
@requireSelf
@log("获取所有AI历史记录")
async def get_all_ai_history(
    request: Request,
    db: DbSession,
    ai_history_service: AiHistoryServiceDep,
    user_id: int = Query(alias="user_id"),
) -> ApiResponse:
    """获取所有AI历史记录接口"""

    histories: list[dict[str, Any]] = await ai_history_service.get_all_ai_history(
        user_id, db
    )
    return success(data=histories)


@router.delete(
    "/{user_id}",
    summary="删除用户所有AI历史记录",
    description="删除指定用户的所有AI历史记录",
    response_model=ApiResponse[None],
)
@requireSelf
@log("删除用户所有AI历史记录")
async def delete_ai_history(
    request: Request,
    db: DbSession,
    ai_history_service: AiHistoryServiceDep,
    user_id: int = Path(alias="user_id"),
) -> ApiResponse:
    """删除用户所有AI历史记录接口"""

    await ai_history_service.delete_ai_history_by_userid(user_id, db)
    return success()
