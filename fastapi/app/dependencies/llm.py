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
from .mappers import AiHistoryMapperDep, AiUserSummaryMapperDep
from .tools import AgentToolFactoriesDep


def provide_gpt_service(
    ai_history_mapper: AiHistoryMapperDep,
    spring_client: SpringClientDep,
    tool_factories: AgentToolFactoriesDep,
    ai_user_summary_mapper: AiUserSummaryMapperDep,
) -> GptService:
    return get_gpt_service(
        ai_history_mapper, spring_client, tool_factories, ai_user_summary_mapper
    )


def provide_gemini_service(
    ai_history_mapper: AiHistoryMapperDep,
    spring_client: SpringClientDep,
    tool_factories: AgentToolFactoriesDep,
    ai_user_summary_mapper: AiUserSummaryMapperDep,
) -> GeminiService:
    return get_gemini_service(
        ai_history_mapper, spring_client, tool_factories, ai_user_summary_mapper
    )


def provide_glm_service(
    ai_history_mapper: AiHistoryMapperDep,
    spring_client: SpringClientDep,
    tool_factories: AgentToolFactoriesDep,
    ai_user_summary_mapper: AiUserSummaryMapperDep,
) -> GlmService:
    return get_glm_service(
        ai_history_mapper, spring_client, tool_factories, ai_user_summary_mapper
    )


GptServiceDep = Annotated[GptService, Depends(provide_gpt_service)]
GeminiServiceDep = Annotated[GeminiService, Depends(provide_gemini_service)]
GlmServiceDep = Annotated[GlmService, Depends(provide_glm_service)]
