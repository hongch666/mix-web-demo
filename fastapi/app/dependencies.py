from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.internal.services import (
    AiHistoryService,
    AlgorithmService,
    AnalyzeService,
    ApiLogService,
    DeepseekService,
    GeminiService,
    GenerateService,
    GptService,
    GraphSearchService,
    UserService,
    VectorSearchService,
    get_ai_history_service,
    get_algorithm_service,
    get_analyze_service,
    get_apilog_service,
    get_deepseek_service,
    get_gemini_service,
    get_generate_service,
    get_gpt_service,
    get_graph_search_service,
    get_user_service,
    get_vector_search_service,
)
from fastapi import Depends

# 数据库会话依赖
DbSession = Annotated[AsyncSession, Depends(get_db)]

# 服务层依赖
AlgorithmServiceDep = Annotated[AlgorithmService, Depends(get_algorithm_service)]
AnalyzeServiceDep = Annotated[AnalyzeService, Depends(get_analyze_service)]
GenerateServiceDep = Annotated[GenerateService, Depends(get_generate_service)]
AiHistoryServiceDep = Annotated[AiHistoryService, Depends(get_ai_history_service)]
ApiLogServiceDep = Annotated[ApiLogService, Depends(get_apilog_service)]
GraphSearchServiceDep = Annotated[GraphSearchService, Depends(get_graph_search_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]

# AI 服务依赖
GptServiceDep = Annotated[GptService, Depends(get_gpt_service)]
GeminiServiceDep = Annotated[GeminiService, Depends(get_gemini_service)]
DeepseekServiceDep = Annotated[DeepseekService, Depends(get_deepseek_service)]

# 搜索服务依赖
VectorSearchServiceDep = Annotated[
    VectorSearchService, Depends(get_vector_search_service)
]
