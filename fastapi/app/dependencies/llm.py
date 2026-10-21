from typing import Annotated

from fastapi import Depends

from app.internal.services import (
    ClaudeService,
    DeepseekService,
    GeminiService,
    GlmService,
    GptService,
    QwenService,
    get_claude_service,
    get_deepseek_service,
    get_gemini_service,
    get_glm_service,
    get_gpt_service,
    get_qwen_service,
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
    """装配 GPT 服务单例，依赖 AI 历史与记忆摘要 Mapper、Spring 客户端及 agent 工具工厂"""
    return get_gpt_service(
        ai_history_mapper, spring_client, tool_factories, ai_user_summary_mapper
    )


def provide_gemini_service(
    ai_history_mapper: AiHistoryMapperDep,
    spring_client: SpringClientDep,
    tool_factories: AgentToolFactoriesDep,
    ai_user_summary_mapper: AiUserSummaryMapperDep,
) -> GeminiService:
    """装配 Gemini 服务单例，依赖 AI 历史与记忆摘要 Mapper、Spring 客户端及 agent 工具工厂"""
    return get_gemini_service(
        ai_history_mapper, spring_client, tool_factories, ai_user_summary_mapper
    )


def provide_glm_service(
    ai_history_mapper: AiHistoryMapperDep,
    spring_client: SpringClientDep,
    tool_factories: AgentToolFactoriesDep,
    ai_user_summary_mapper: AiUserSummaryMapperDep,
) -> GlmService:
    """装配 GLM 服务单例，依赖 AI 历史与记忆摘要 Mapper、Spring 客户端及 agent 工具工厂"""
    return get_glm_service(
        ai_history_mapper, spring_client, tool_factories, ai_user_summary_mapper
    )


def provide_deepseek_service(
    ai_history_mapper: AiHistoryMapperDep,
    spring_client: SpringClientDep,
    tool_factories: AgentToolFactoriesDep,
    ai_user_summary_mapper: AiUserSummaryMapperDep,
) -> DeepseekService:
    """装配 DeepSeek 服务单例，依赖 AI 历史与记忆摘要 Mapper、Spring 客户端及 agent 工具工厂"""
    return get_deepseek_service(
        ai_history_mapper, spring_client, tool_factories, ai_user_summary_mapper
    )


def provide_claude_service(
    ai_history_mapper: AiHistoryMapperDep,
    spring_client: SpringClientDep,
    tool_factories: AgentToolFactoriesDep,
    ai_user_summary_mapper: AiUserSummaryMapperDep,
) -> ClaudeService:
    """装配 Claude 服务单例，依赖 AI 历史与记忆摘要 Mapper、Spring 客户端及 agent 工具工厂"""
    return get_claude_service(
        ai_history_mapper, spring_client, tool_factories, ai_user_summary_mapper
    )


def provide_qwen_service(
    ai_history_mapper: AiHistoryMapperDep,
    spring_client: SpringClientDep,
    tool_factories: AgentToolFactoriesDep,
    ai_user_summary_mapper: AiUserSummaryMapperDep,
) -> QwenService:
    """装配 Qwen 服务单例，依赖 AI 历史与记忆摘要 Mapper、Spring 客户端及 agent 工具工厂"""
    return get_qwen_service(
        ai_history_mapper, spring_client, tool_factories, ai_user_summary_mapper
    )


GptServiceDep = Annotated[GptService, Depends(provide_gpt_service)]
GeminiServiceDep = Annotated[GeminiService, Depends(provide_gemini_service)]
GlmServiceDep = Annotated[GlmService, Depends(provide_glm_service)]
DeepseekServiceDep = Annotated[DeepseekService, Depends(provide_deepseek_service)]
ClaudeServiceDep = Annotated[ClaudeService, Depends(provide_claude_service)]
QwenServiceDep = Annotated[QwenService, Depends(provide_qwen_service)]
