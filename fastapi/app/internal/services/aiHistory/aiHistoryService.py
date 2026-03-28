import hashlib
import time
from functools import lru_cache
from typing import Any, Dict, Optional

from app.core.base import Constants
from app.core.errors import BusinessException
from app.internal.crud import (
    AiHistoryMapper,
    UserMapper,
    get_ai_history_mapper,
    get_user_mapper,
)
from app.internal.models import AiHistory

from fastapi import Depends


class AiHistoryService:
    """AI 历史记录 Service"""

    def __init__(
        self,
        ai_history_mapper: Optional[AiHistoryMapper] = None,
        user_mapper: Optional[UserMapper] = None,
    ):
        self.ai_history_mapper: Optional[AiHistoryMapper] = ai_history_mapper
        self.user_mapper: Optional[UserMapper] = user_mapper
        # 用于短时间去重的缓存
        self._request_cache: Dict[str, float] = {}

    def create_ai_history(self, ai_history: Any, db: Any) -> Any:
        data = ai_history.dict() if hasattr(ai_history, "dict") else dict(ai_history)

        # 方案1：基于内容和用户ID生成唯一键进行去重（5秒内相同请求只处理一次）
        request_key = hashlib.md5(
            f"{data['user_id']}:{data['ask']}:{data['reply']}".encode()
        ).hexdigest()

        current_time = time.time()
        if request_key in self._request_cache:
            last_time = self._request_cache[request_key]
            if current_time - last_time < 5:  # 5秒内的重复请求
                return {"status": "duplicate", "message": Constants.REQUEST_PROCESSING}

        self._request_cache[request_key] = current_time

        # 清理过期缓存（保留最近10秒的记录）
        self._request_cache = {
            k: v for k, v in self._request_cache.items() if current_time - v < 10
        }

        history = AiHistory(
            user_id=data["user_id"],
            ask=data["ask"],
            reply=data["reply"],
            thinking=data.get("thinking"),
            ai_type=data["ai_type"],
        )

        return self.ai_history_mapper.create_ai_history(history, db)

    def get_all_ai_history(self, user_id: int, db: Any) -> list[Dict[str, Any]]:
        data = self.ai_history_mapper.get_all_ai_history_by_userid(
            db, user_id=user_id, limit=None
        )
        return [self._serialize_ai_history(item) for item in data]

    def delete_ai_history_by_userid(self, user_id: int, db: Any) -> None:
        # 检查用户是否存在
        user = self.user_mapper.get_user_by_id(user_id, db)
        if not user:
            raise BusinessException(Constants.USER_NOT_EXISTS_ERROR)

        self.ai_history_mapper.delete_ai_history_by_userid(db, user_id)

    @staticmethod
    def _serialize_ai_history(ai_history: AiHistory) -> Dict[str, Any]:
        """将 ORM 对象转换为可序列化的响应字典。"""
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


@lru_cache
def get_ai_history_service(
    ai_history_mapper: AiHistoryMapper = Depends(get_ai_history_mapper),
    user_mapper: UserMapper = Depends(get_user_mapper),
) -> AiHistoryService:
    return AiHistoryService(ai_history_mapper, user_mapper)
