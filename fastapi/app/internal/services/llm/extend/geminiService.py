from functools import lru_cache
from typing import Optional

from app.internal.crud import (
    AiHistoryMapper,
    UserMapper,
    get_ai_history_mapper,
    get_user_mapper,
)

from fastapi import Depends

from ..baseAIService import BaseAiService


class GeminiService(BaseAiService):
    """Gemini 模型服务"""

    def __init__(
        self,
        ai_history_mapper: AiHistoryMapper,
        user_mapper: Optional[UserMapper] = None,
    ) -> None:
        super().__init__(
            ai_history_mapper,
            service_name="Gemini",
            config_section="closeai",
            model_config_key="gemini_model_name",
            user_mapper=user_mapper,
        )


@lru_cache()
def get_gemini_service(
    ai_history_mapper: AiHistoryMapper = Depends(get_ai_history_mapper),
    user_mapper: UserMapper = Depends(get_user_mapper),
) -> GeminiService:
    """获取 Gemini 服务单例实例"""
    return GeminiService(ai_history_mapper, user_mapper)
