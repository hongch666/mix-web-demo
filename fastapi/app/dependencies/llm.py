from typing import Annotated

from fastapi import Depends

from app.internal.services import (
    GeminiService,
    GlmService,
    GptService,
    get_gemini_service,
    get_glm_service,
    get_gpt_service,
)

from .clients import SpringClientDep
from .mappers import AiHistoryMapperDep
from .tools import AgentToolFactoriesDep


def provide_gpt_service(
    ai_history_mapper: AiHistoryMapperDep,
    spring_client: SpringClientDep,
    tool_factories: AgentToolFactoriesDep,
) -> GptService:
    return get_gpt_service(ai_history_mapper, spring_client, tool_factories)


def provide_gemini_service(
    ai_history_mapper: AiHistoryMapperDep,
    spring_client: SpringClientDep,
    tool_factories: AgentToolFactoriesDep,
) -> GeminiService:
    return get_gemini_service(ai_history_mapper, spring_client, tool_factories)


def provide_glm_service(
    ai_history_mapper: AiHistoryMapperDep,
    spring_client: SpringClientDep,
    tool_factories: AgentToolFactoriesDep,
) -> GlmService:
    return get_glm_service(ai_history_mapper, spring_client, tool_factories)


GptServiceDep = Annotated[GptService, Depends(provide_gpt_service)]
GeminiServiceDep = Annotated[GeminiService, Depends(provide_gemini_service)]
GlmServiceDep = Annotated[GlmService, Depends(provide_glm_service)]
