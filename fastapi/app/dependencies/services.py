from typing import Annotated

from fastapi import Depends

from app.internal.cache import (
    get_article_cache,
    get_category_cache,
    get_publish_time_cache,
    get_statistics_cache,
    get_wordcloud_cache,
)
from app.internal.clients import get_nestjs_client, get_spring_client
from app.internal.services import (
    AiHistoryService,
    AlgorithmService,
    AnalyzeService,
    ApiLogService,
    ChatApplicationService,
    ChatService,
    GenerateService,
    GraphSearchService,
    TaskService,
    UserService,
    VectorSearchService,
    get_ai_history_service,
    get_algorithm_service,
    get_analyze_service,
    get_apilog_service,
    get_chat_application_service,
    get_chat_service,
    get_generate_service,
    get_graph_search_service,
    get_task_service,
    get_user_service,
    get_vector_search_service,
)

from .caches import (
    ArticleCacheDep,
    CategoryCacheDep,
    PublishTimeCacheDep,
    StatisticsCacheDep,
    WordcloudCacheDep,
)
from .clients import NestjsClientDep, SpringClientDep
from .database import DbSessionFactoryDep
from .llm import (
    ClaudeServiceDep,
    DeepseekServiceDep,
    GeminiServiceDep,
    GlmServiceDep,
    GptServiceDep,
    QwenServiceDep,
)
from .logger import LoggerDep
from .mappers import (
    AiHistoryMapperDep,
    AiUserSummaryMapperDep,
    ApiLogMapperDep,
    ArticleMapperDep,
    UserMapperDep,
    VectorMapperDep,
    resolve_article_mapper,
)


def provide_algorithm_service() -> AlgorithmService:
    """装配搜索算法服务单例，无外部依赖"""
    return get_algorithm_service()


def provide_chat_service() -> ChatService:
    """装配基础聊天服务单例，无外部依赖"""
    return get_chat_service()


def provide_analyze_service(
    article_mapper: ArticleMapperDep,
    article_cache: ArticleCacheDep,
    category_cache: CategoryCacheDep,
    publish_time_cache: PublishTimeCacheDep,
    statistics_cache: StatisticsCacheDep,
    wordcloud_cache: WordcloudCacheDep,
    spring_client: SpringClientDep,
    nestjs_client: NestjsClientDep,
    logger: LoggerDep,
) -> AnalyzeService:
    """装配数据分析服务单例，依赖文章数仓 Mapper、五类缓存及 Spring 与 NestJS 客户端"""
    return get_analyze_service(
        article_mapper,
        article_cache,
        category_cache,
        publish_time_cache,
        statistics_cache,
        wordcloud_cache,
        spring_client,
        nestjs_client,
        logger,
    )


def resolve_analyze_service() -> AnalyzeService:
    """请求外（调度器等）通过依赖图解析 AnalyzeService

    参数取自与 provide_analyze_service 相同的单例工厂，
    因此返回的是与请求路径完全相同的实例，singleflight 锁等内部状态共享
    """
    return get_analyze_service(
        resolve_article_mapper(),
        get_article_cache(),
        get_category_cache(),
        get_publish_time_cache(),
        get_statistics_cache(),
        get_wordcloud_cache(),
        get_spring_client(),
        get_nestjs_client(),
    )


def provide_generate_service(
    glm_service: GlmServiceDep,
    gemini_service: GeminiServiceDep,
    gpt_service: GptServiceDep,
    deepseek_service: DeepseekServiceDep,
    claude_service: ClaudeServiceDep,
    qwen_service: QwenServiceDep,
    spring_client: SpringClientDep,
    logger: LoggerDep,
) -> GenerateService:
    """装配 AI 内容生成服务单例，依赖六个大模型服务与 Spring 客户端"""
    return get_generate_service(
        glm_service,
        gemini_service,
        gpt_service,
        deepseek_service,
        claude_service,
        qwen_service,
        spring_client,
        logger,
    )


def provide_ai_history_service(
    ai_history_mapper: AiHistoryMapperDep,
    spring_client: SpringClientDep,
    ai_user_summary_mapper: AiUserSummaryMapperDep,
    logger: LoggerDep,
) -> AiHistoryService:
    """装配 AI 历史服务单例，依赖历史与记忆摘要 Mapper 及 Spring 客户端"""
    return get_ai_history_service(
        ai_history_mapper, spring_client, ai_user_summary_mapper, logger
    )


def provide_api_log_service(
    nestjs_client: NestjsClientDep,
    api_log_mapper: ApiLogMapperDep,
    logger: LoggerDep,
) -> ApiLogService:
    """装配 API 日志服务单例，依赖 NestJS 客户端与 API 日志数仓 Mapper"""
    return get_apilog_service(nestjs_client, api_log_mapper, logger)


def provide_graph_search_service(logger: LoggerDep) -> GraphSearchService:
    """装配知识图谱检索服务单例，logger 由 FastAPI 依赖注入提供"""
    return get_graph_search_service(logger)


def provide_user_service(
    spring_client: SpringClientDep,
    nestjs_client: NestjsClientDep,
    user_mapper: UserMapperDep,
    logger: LoggerDep,
) -> UserService:
    """装配用户分析服务单例，依赖 Spring 与 NestJS 客户端及用户数仓 Mapper"""
    return get_user_service(spring_client, nestjs_client, user_mapper, logger)


def provide_vector_search_service(
    vector_mapper: VectorMapperDep,
    logger: LoggerDep,
) -> VectorSearchService:
    """装配向量检索服务单例，依赖向量库 Mapper"""
    return get_vector_search_service(vector_mapper, logger)


def provide_task_service(
    analyze_service: AnalyzeService,
    db_factory: DbSessionFactoryDep,
    spring_client: SpringClientDep,
    nestjs_client: NestjsClientDep,
) -> TaskService:
    """装配定时任务触发服务单例，依赖分析服务、MySQL 会话工厂与 Spring/NestJS 客户端"""
    return get_task_service(analyze_service, db_factory, spring_client, nestjs_client)


AlgorithmServiceDep = Annotated[AlgorithmService, Depends(provide_algorithm_service)]
ChatServiceDep = Annotated[ChatService, Depends(provide_chat_service)]
AnalyzeServiceDep = Annotated[AnalyzeService, Depends(provide_analyze_service)]
GenerateServiceDep = Annotated[GenerateService, Depends(provide_generate_service)]
AiHistoryServiceDep = Annotated[AiHistoryService, Depends(provide_ai_history_service)]


def provide_chat_application_service(
    gpt_service: GptServiceDep,
    gemini_service: GeminiServiceDep,
    glm_service: GlmServiceDep,
    deepseek_service: DeepseekServiceDep,
    claude_service: ClaudeServiceDep,
    qwen_service: QwenServiceDep,
    history_service: AiHistoryServiceDep,
    logger: LoggerDep,
) -> ChatApplicationService:
    """装配聊天应用服务单例，依赖六个大模型服务与 AI 历史服务"""
    return get_chat_application_service(
        gpt_service,
        gemini_service,
        glm_service,
        deepseek_service,
        claude_service,
        qwen_service,
        history_service,
        logger,
    )


ChatApplicationServiceDep = Annotated[
    ChatApplicationService, Depends(provide_chat_application_service)
]
ApiLogServiceDep = Annotated[ApiLogService, Depends(provide_api_log_service)]
GraphSearchServiceDep = Annotated[
    GraphSearchService, Depends(provide_graph_search_service)
]
UserServiceDep = Annotated[UserService, Depends(provide_user_service)]
VectorSearchServiceDep = Annotated[
    VectorSearchService, Depends(provide_vector_search_service)
]
TaskServiceDep = Annotated[TaskService, Depends(provide_task_service)]
