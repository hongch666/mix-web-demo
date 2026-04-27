from functools import lru_cache
from typing import Optional

from app.internal.crud import (
    AiHistoryMapper,
    UserMapper,
    get_ai_history_mapper,
    get_user_mapper,
)

from fastapi import Depends

from .baseAIService import BaseAiService


class GptService(BaseAiService):
    """GPT 模型服务"""

    def __init__(
        self,
        ai_history_mapper: AiHistoryMapper,
        user_mapper: Optional[UserMapper] = None,
    ) -> None:
        super().__init__(
            ai_history_mapper,
            service_name="GPT",
            config_section="closeai",
            model_config_key="gpt_model_name",
            user_mapper=user_mapper,
        )


@lru_cache()
def get_gpt_service(
    ai_history_mapper: AiHistoryMapper = Depends(get_ai_history_mapper),
    user_mapper: UserMapper = Depends(get_user_mapper),
) -> GptService:
    """获取 GPT 服务单例实例"""
    return GptService(ai_history_mapper, user_mapper)
