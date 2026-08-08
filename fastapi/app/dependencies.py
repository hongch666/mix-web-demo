"""FastAPI 依赖注入类型别名

使用 Annotated 模式简化依赖注入声明，避免在每个路由中重复写 Depends()
"""

from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.internal.crud import (
    ArticleMapper,
    CommentsMapper,
    get_article_mapper,
    get_comments_mapper,
)
from app.internal.services import (
    AiHistoryService,
    AnalyzeService,
    ApiLogService,
    DeepseekService,
    GeminiService,
    GenerateService,
    GptService,
    GraphSearchService,
    UserService,
    get_ai_history_service,
    get_analyze_service,
    get_apilog_service,
    get_deepseek_service,
    get_gemini_service,
    get_generate_service,
    get_gpt_service,
    get_graph_search_service,
    get_user_service,
)
from app.internal.services.vectorSearch import (
    VectorSearchService,
    get_vector_search_service,
)
from fastapi import Depends

# 数据库会话依赖
DbSession = Annotated[AsyncSession, Depends(get_db)]

# 服务层依赖
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

# CRUD Mapper 依赖
ArticleMapperDep = Annotated[ArticleMapper, Depends(get_article_mapper)]
CommentsMapperDep = Annotated[CommentsMapper, Depends(get_comments_mapper)]
