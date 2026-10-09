from functools import lru_cache
from typing import Optional

from app.internal.agents import AgentToolFactories
from app.internal.clients import SpringClient, get_spring_client
from app.internal.crud import AiHistoryMapper, AiUserSummaryMapper

from ..baseAIService import BaseAiService


class GeminiService(BaseAiService):
    """Gemini 模型服务"""

    def __init__(
        self,
        ai_history_mapper: AiHistoryMapper,
        spring_client: Optional[SpringClient] = None,
        tool_factories: Optional[AgentToolFactories] = None,
        ai_user_summary_mapper: Optional[AiUserSummaryMapper] = None,
    ) -> None:
        super().__init__(
            ai_history_mapper,
            service_name="Gemini",
            config_section="closeai",
            model_config_key="gemini_model_name",
            tool_factories=tool_factories,
            ai_user_summary_mapper=ai_user_summary_mapper,
        )
        self._spring_client: SpringClient = spring_client or get_spring_client()


@lru_cache
def get_gemini_service(
    ai_history_mapper: AiHistoryMapper,
    spring_client: SpringClient,
    tool_factories: Optional[AgentToolFactories] = None,
    ai_user_summary_mapper: Optional[AiUserSummaryMapper] = None,
) -> GeminiService:
    """获取 Gemini 服务单例实例"""
    return GeminiService(
        ai_history_mapper, spring_client, tool_factories, ai_user_summary_mapper
    )
