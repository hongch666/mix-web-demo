from functools import lru_cache
from typing import Any, Dict, List, Optional

from app.core.constants import HttpCode, Messages
from app.core.errors import BusinessException
from app.internal.clients import SpringClient
from app.internal.crud import (
    AiHistoryMapper,
    get_ai_history_mapper,
)
from app.internal.models import AiHistory

from fastapi import Depends


class AiHistoryService:
    """AI 历史记录 Service"""

    def __init__(
        self,
        ai_history_mapper: Optional[AiHistoryMapper] = None,
    ) -> None:
        self.ai_history_mapper: Optional[AiHistoryMapper] = ai_history_mapper
        self._spring_client: SpringClient = SpringClient()

    async def create_ai_history(self, ai_history: Any, db: Any) -> Any:
        data: Dict[str, Any] = self._normalize_ai_history_data(ai_history)
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

    async def get_all_ai_history(self, user_id: int, db: Any) -> list[Dict[str, Any]]:
        data: List[
            Dict[str, Any]
        ] = await self.ai_history_mapper.get_all_ai_history_by_userid_async(
            db, user_id, None
        )
        return [self._serialize_ai_history(item) for item in data]

    async def delete_ai_history_by_userid(self, user_id: int, db: Any) -> None:
        # 检查用户是否存在（通过SpringClient远程查询）
        users = await self._spring_client.get_users_by_ids([user_id])
        if not users:
            raise BusinessException(
                Messages.USER_NOT_EXISTS_ERROR,
                HttpCode.NOT_FOUND,
                Messages.ERROR_USER_NOT_FOUND,
            )

        await self.ai_history_mapper.delete_ai_history_by_userid_async(db, user_id)

    async def get_ai_history_by_id(self, id: int, db: Any) -> Optional[Dict[str, Any]]:
        """根据ID查询AI历史记录"""
        history = await self.ai_history_mapper.get_ai_history_by_id_async(db, id)
        if not history:
            return None
        return self._serialize_ai_history(history)

    async def update_ai_history(
        self, id: int, data: Any, db: Any
    ) -> Optional[Dict[str, Any]]:
        """更新AI历史记录"""
        history = await self.ai_history_mapper.get_ai_history_by_id_async(db, id)
        if not history:
            return None

        # 更新字段
        normalized_data = self._normalize_ai_history_data(data)
        if "user_id" in normalized_data:
            history.user_id = normalized_data["user_id"]
        if "ask" in normalized_data:
            history.ask = normalized_data["ask"]
        if "reply" in normalized_data:
            history.reply = normalized_data["reply"]
        if "thinking" in normalized_data:
            thinking = normalized_data["thinking"]
            history.thinking = thinking if thinking != "" else None
        if "ai_type" in normalized_data:
            history.ai_type = normalized_data["ai_type"]

        updated = await self.ai_history_mapper.update_ai_history_async(db, history)
        return self._serialize_ai_history(updated)

    async def delete_ai_history_by_id(self, id: int, db: Any) -> bool:
        """根据ID删除AI历史记录"""
        history = await self.ai_history_mapper.get_ai_history_by_id_async(db, id)
        if not history:
            return False
        await self.ai_history_mapper.delete_ai_history_by_id_async(db, id)
        return True

    @staticmethod
    def _serialize_ai_history(ai_history: AiHistory) -> Dict[str, Any]:
        """将 ORM 对象转换为可序列化的响应字典"""
        fmt = "%Y-%m-%d %H:%M:%S"
        return {
            "id": ai_history.id,
            "user_id": ai_history.user_id,
            "ask": ai_history.ask,
            "reply": ai_history.reply,
            "thinking": ai_history.thinking,
            "ai_type": ai_history.ai_type,
            "created_at": ai_history.created_at.strftime(fmt)
            if getattr(ai_history, "created_at", None)
            else None,
            "updated_at": ai_history.updated_at.strftime(fmt)
            if getattr(ai_history, "updated_at", None)
            else None,
        }

    @staticmethod
    def _normalize_ai_history_data(ai_history: Any) -> Dict[str, Any]:
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
    ai_history_mapper: AiHistoryMapper = Depends(get_ai_history_mapper),
) -> AiHistoryService:
    return AiHistoryService(ai_history_mapper)
