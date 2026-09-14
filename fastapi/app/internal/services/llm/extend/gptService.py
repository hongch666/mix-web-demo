from functools import lru_cache
from typing import Optional

from app.internal.clients import SpringClient, get_spring_client
from app.internal.crud import (
    AiHistoryMapper,
    get_ai_history_mapper,
)

from fastapi import Depends

from ..baseAIService import BaseAiService


class GptService(BaseAiService):
    """GPT 模型服务"""

    def __init__(
        self,
        ai_history_mapper: AiHistoryMapper,
        spring_client: Optional[SpringClient] = None,
    ) -> None:
        super().__init__(
            ai_history_mapper,
            service_name="GPT",
            config_section="closeai",
            model_config_key="gpt_model_name",
        )
        self._spring_client: SpringClient = spring_client or get_spring_client()


@lru_cache()
def get_gpt_service(
    ai_history_mapper: AiHistoryMapper = Depends(get_ai_history_mapper),
) -> GptService:
    """获取 GPT 服务单例实例"""
    return GptService(ai_history_mapper, get_spring_client())
