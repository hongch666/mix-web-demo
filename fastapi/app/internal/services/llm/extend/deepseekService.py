from functools import lru_cache
from typing import Optional

from app.internal.agents import AgentToolFactories
from app.internal.clients import SpringClient, get_spring_client
from app.internal.crud import AiHistoryMapper, AiUserSummaryMapper

from ..baseAIService import BaseAiService


class DeepseekService(BaseAiService):
    """DeepSeek 模型服务"""

    def __init__(
        self,
        ai_history_mapper: AiHistoryMapper,
        spring_client: Optional[SpringClient] = None,
        tool_factories: Optional[AgentToolFactories] = None,
        ai_user_summary_mapper: Optional[AiUserSummaryMapper] = None,
    ) -> None:
        """以 DeepSeek 服务名与模型配置键初始化基类，并注入 Spring 客户端"""
        super().__init__(
            ai_history_mapper,
            service_name="DeepSeek",
            config_section="closeai",
            model_config_key="deepseek_model_name",
            tool_factories=tool_factories,
            ai_user_summary_mapper=ai_user_summary_mapper,
        )
        self._spring_client: SpringClient = spring_client or get_spring_client()


@lru_cache
def get_deepseek_service(
    ai_history_mapper: AiHistoryMapper,
    spring_client: SpringClient,
    tool_factories: Optional[AgentToolFactories] = None,
    ai_user_summary_mapper: Optional[AiUserSummaryMapper] = None,
) -> DeepseekService:
    """获取 DeepSeek 服务单例实例"""
    return DeepseekService(
        ai_history_mapper, spring_client, tool_factories, ai_user_summary_mapper
    )
