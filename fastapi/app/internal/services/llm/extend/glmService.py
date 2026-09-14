from functools import lru_cache
from typing import Optional

from app.internal.clients import SpringClient, get_spring_client
from app.internal.crud import (
    AiHistoryMapper,
    get_ai_history_mapper,
)

from fastapi import Depends

from ..baseAIService import BaseAiService


class GlmService(BaseAiService):
    """GLM 模型服务"""

    def __init__(
        self,
        ai_history_mapper: AiHistoryMapper,
        spring_client: Optional[SpringClient] = None,
    ) -> None:
        super().__init__(
            ai_history_mapper,
            service_name="GLM",
            config_section="closeai",
            model_config_key="glm_model_name",
            use_structured_output=False,
        )
        self._spring_client: SpringClient = spring_client or get_spring_client()


@lru_cache()
def get_glm_service(
    ai_history_mapper: AiHistoryMapper = Depends(get_ai_history_mapper),
) -> GlmService:
    """获取 GLM 服务单例实例"""
    return GlmService(ai_history_mapper, get_spring_client())
