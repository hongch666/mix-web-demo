from functools import lru_cache

from app.internal.schemas import AIServiceType


class ChatService:
    """AI聊天服务"""

    def get_available_models(self) -> list[str]:
        """获取当前支持的聊天模型枚举值列表，元素即聊天请求 service 参数的合法取值"""
        return [service.value for service in AIServiceType]


@lru_cache
def get_chat_service() -> ChatService:
    return ChatService()
