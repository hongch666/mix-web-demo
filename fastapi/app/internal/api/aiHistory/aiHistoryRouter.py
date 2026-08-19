from typing import Any

from app.common.decorators import log, requireInternalToken
from app.core.base import ApiResponse, success
from app.dependencies import AiHistoryServiceDep, DbSession
from app.internal.schemas import CreateHistoryDTO, UpdateHistoryDTO

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


@router.get(
    "/internal/{id}",
    summary="根据ID查询AI历史记录（内部）",
    description="根据ID查询AI历史记录，供内部服务远程调用",
    response_model=ApiResponse,
)
@requireInternalToken
@log("内部查询AI历史记录")
async def get_ai_history_by_id_internal(
    request: Request,
    db: DbSession,
    ai_history_service: AiHistoryServiceDep,
    id: int = Path(description="AI历史记录ID"),
) -> ApiResponse:
    """根据ID查询AI历史记录（内部接口）"""

    history = await ai_history_service.get_ai_history_by_id(id, db)
    if not history:
        return success(data=None)
    return success(data=history)


@router.put(
    "/internal/{id}",
    summary="更新AI历史记录（内部）",
    description="更新AI历史记录，供内部服务远程调用",
    response_model=ApiResponse,
)
@requireInternalToken
@log("内部更新AI历史记录")
async def update_ai_history_internal(
    request: Request,
    data: UpdateHistoryDTO,
    db: DbSession,
    ai_history_service: AiHistoryServiceDep,
    id: int = Path(description="AI历史记录ID"),
) -> ApiResponse:
    """更新AI历史记录（内部接口）"""

    history = await ai_history_service.update_ai_history(id, data, db)
    if not history:
        return success(data=None)
    return success(data=history)


@router.delete(
    "/internal/{id}",
    summary="删除AI历史记录（内部）",
    description="根据ID删除AI历史记录，供内部服务远程调用",
    response_model=ApiResponse,
)
@requireInternalToken
@log("内部删除AI历史记录")
async def delete_ai_history_internal(
    request: Request,
    db: DbSession,
    ai_history_service: AiHistoryServiceDep,
    id: int = Path(description="AI历史记录ID"),
) -> ApiResponse:
    """删除AI历史记录（内部接口）"""

    deleted = await ai_history_service.delete_ai_history_by_id(id, db)
    return success(data={"deleted": deleted})
