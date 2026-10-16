from collections.abc import Mapping
from functools import lru_cache
from typing import Any

from app.core.auth import is_memory_user
from app.internal.models import AiHistory
from app.internal.schemas import AIServiceType


class ChatService:
    """AI聊天服务"""

    def get_available_models(self) -> list[str]:
        """获取当前支持的聊天模型枚举值列表，元素即聊天请求 service 参数的合法取值"""
        return [service.value for service in AIServiceType]


def select_chat_model[ChatModel](
    service: AIServiceType, models: Mapping[AIServiceType, ChatModel]
) -> ChatModel:
    """按请求中的模型类型选择已注入的模型服务"""
    return models[service]


async def persist_chat_history(
    history_service: Any,
    db: Any,
    user_id: str,
    ask: str,
    reply: str,
    thinking: str | None,
    service: AIServiceType,
) -> bool:
    """保存真实用户的聊天记录，系统调用不写入共享记忆"""
    if not is_memory_user(user_id):
        return False

    history = AiHistory(
        user_id=int(user_id),
        ask=ask,
        reply=reply,
        thinking=thinking or None,
        ai_type=service.value,
    )
    await history_service.create_ai_history(history, db)
    return True


@lru_cache
def get_chat_service() -> ChatService:
    return ChatService()
