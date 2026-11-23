from functools import lru_cache
from typing import Any, Optional

from app.core.base import LoggerProtocol
from app.core.constants import HttpCode, Messages
from app.core.errors import BusinessException
from app.internal.clients import SpringClient
from app.internal.crud import AiHistoryMapper, AiUserSummaryMapper
from app.internal.models import AiHistory
from app.internal.schemas import AiHistoryResponse


class AiHistoryService:
    """AI 历史记录 Service"""

    def __init__(
        self,
        ai_history_mapper: AiHistoryMapper,
        spring_client: SpringClient,
        ai_user_summary_mapper: AiUserSummaryMapper,
        logger: LoggerProtocol,
    ) -> None:
        """注入 AI 历史 Mapper、Spring 客户端、用户记忆摘要 Mapper 与日志器"""
        self.ai_history_mapper: AiHistoryMapper = ai_history_mapper
        self._spring_client: SpringClient = spring_client
        self._ai_user_summary_mapper: AiUserSummaryMapper = ai_user_summary_mapper
        self._logger: LoggerProtocol = logger

    async def create_ai_history(self, ai_history: Any, db: Any) -> Any:
        """归一化入参后构建 AiHistory 实体并写入数据库，空 thinking 统一置为 NULL"""
        data: dict[str, Any] = self._normalize_ai_history_data(ai_history)
        thinking: Optional[Any] = data.get("thinking")
        if thinking == "":
            thinking = None

        history: AiHistory = AiHistory(
            user_id=data["user_id"],
            ask=data["ask"],
            reply=data["reply"],
            thinking=thinking,
            ai_type=data["ai_type"],
        )

        return await self.ai_history_mapper.create_ai_history_async(history, db)

    async def get_all_ai_history(
        self, user_id: int, db: Any
    ) -> list[AiHistoryResponse]:
        """查询指定用户的全部 AI 历史并序列化为响应模型列表"""
        histories = await self.ai_history_mapper.get_all_ai_history_by_userid_async(
            db, user_id, None
        )
        return [self._serialize_ai_history(item) for item in histories]

    async def delete_ai_history_by_userid(self, user_id: int, db: Any) -> None:
        """校验用户存在后在同一事务内删除其 AI 历史与记忆摘要，失败整体回滚"""

        # 检查用户是否存在（通过SpringClient远程查询）
        users = await self._spring_client.get_users_by_ids([user_id])
        if not users:
            raise BusinessException(
                Messages.USER_NOT_EXISTS_ERROR,
                HttpCode.NOT_FOUND,
                Messages.ERROR_USER_NOT_FOUND,
            )

        # 摘要与原文必须同步清理，否则会出现用户已清空历史但记忆仍在的情况，两次删除放入同一事务，任一失败整体回滚
        try:
            await self.ai_history_mapper.delete_ai_history_by_userid_async(db, user_id)
            await self._ai_user_summary_mapper.delete_by_user_id_async(db, user_id)
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        self._logger.info(Messages.AI_MEMORY_SUMMARY_CLEARED(user_id))

    @staticmethod
    def _serialize_ai_history(ai_history: AiHistory) -> AiHistoryResponse:
        """将 ORM 对象转换为具名响应模型"""
        fmt = "%Y-%m-%d %H:%M:%S"
        history_id = ai_history.id
        user_id = ai_history.user_id
        if history_id is None or user_id is None:
            raise ValueError(Messages.AI_HISTORY_REQUIRED_ID_MISSING)

        created_at = ai_history.created_at
        updated_at = ai_history.updated_at
        return AiHistoryResponse(
            id=history_id,
            user_id=user_id,
            ask=ai_history.ask,
            reply=ai_history.reply,
            thinking=ai_history.thinking,
            ai_type=ai_history.ai_type,
            created_at=created_at.strftime(fmt) if created_at is not None else None,
            updated_at=updated_at.strftime(fmt) if updated_at is not None else None,
        )

    @staticmethod
    def _normalize_ai_history_data(ai_history: Any) -> dict[str, Any]:
        """统一兼容 ORM 实体、Pydantic 模型和字典对象"""
        if isinstance(ai_history, AiHistory):
            return {
                "user_id": ai_history.user_id,
                "ask": ai_history.ask,
                "reply": ai_history.reply,
                "thinking": ai_history.thinking,
                "ai_type": ai_history.ai_type,
            }

        if hasattr(ai_history, "model_dump"):
            return ai_history.model_dump(by_alias=True)

        if hasattr(ai_history, "dict"):
            return ai_history.dict()

        return dict(ai_history)


@lru_cache
def get_ai_history_service(
    ai_history_mapper: AiHistoryMapper,
    spring_client: SpringClient,
    ai_user_summary_mapper: AiUserSummaryMapper,
    logger: LoggerProtocol,
) -> AiHistoryService:
    """按依赖参数缓存并返回 AiHistoryService 单例"""
    return AiHistoryService(
        ai_history_mapper,
        spring_client,
        ai_user_summary_mapper,
        logger,
    )
