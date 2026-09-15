from functools import lru_cache
from typing import Optional

from app.internal.agents import AgentToolFactories
from app.internal.clients import SpringClient, get_spring_client
from app.internal.crud import (
    AiHistoryMapper,
)

from ..baseAIService import BaseAiService


class GptService(BaseAiService):
    """GPT 模型服务"""

    def __init__(
        self,
        ai_history_mapper: AiHistoryMapper,
        spring_client: Optional[SpringClient] = None,
        tool_factories: Optional[AgentToolFactories] = None,
    ) -> None:
        super().__init__(
            ai_history_mapper,
            service_name="GPT",
            config_section="closeai",
            model_config_key="gpt_model_name",
            tool_factories=tool_factories,
        )
        self._spring_client: SpringClient = spring_client or get_spring_client()


@lru_cache()
def get_gpt_service(
    ai_history_mapper: AiHistoryMapper,
    spring_client: SpringClient,
    tool_factories: Optional[AgentToolFactories] = None,
) -> GptService:
    """获取 GPT 服务单例实例"""
    return GptService(ai_history_mapper, spring_client, tool_factories)
