from typing import Annotated

from fastapi import Depends

from app.internal.cache import (
    get_article_cache,
    get_category_cache,
    get_publish_time_cache,
    get_statistics_cache,
    get_wordcloud_cache,
)
from app.internal.clients import (
    get_nestjs_client,
    get_spring_client,
)
from app.internal.services import (
    AiHistoryService,
    AlgorithmService,
    AnalyzeService,
    ApiLogService,
    GenerateService,
    GraphSearchService,
    UserService,
    VectorSearchService,
    get_ai_history_service,
    get_algorithm_service,
    get_analyze_service,
    get_apilog_service,
    get_generate_service,
    get_graph_search_service,
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
from .llm import GeminiServiceDep, GlmServiceDep, GptServiceDep
from .mappers import (
    AiHistoryMapperDep,
    ApiLogMapperDep,
    ArticleMapperDep,
    UserMapperDep,
    resolve_article_mapper,
)
from .tools import RAGToolsDep


def provide_algorithm_service() -> AlgorithmService:
    return get_algorithm_service()


def provide_analyze_service(
    article_mapper: ArticleMapperDep,
    article_cache: ArticleCacheDep,
    category_cache: CategoryCacheDep,
    publish_time_cache: PublishTimeCacheDep,
    statistics_cache: StatisticsCacheDep,
    wordcloud_cache: WordcloudCacheDep,
    spring_client: SpringClientDep,
    nestjs_client: NestjsClientDep,
) -> AnalyzeService:
    return get_analyze_service(
        article_mapper,
        article_cache,
        category_cache,
        publish_time_cache,
        statistics_cache,
        wordcloud_cache,
        spring_client,
        nestjs_client,
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
    spring_client: SpringClientDep,
) -> GenerateService:
    return get_generate_service(
        glm_service,
        gemini_service,
        gpt_service,
        spring_client,
    )


def provide_ai_history_service(
    ai_history_mapper: AiHistoryMapperDep,
    spring_client: SpringClientDep,
) -> AiHistoryService:
    return get_ai_history_service(ai_history_mapper, spring_client)


def provide_api_log_service(
    nestjs_client: NestjsClientDep,
    api_log_mapper: ApiLogMapperDep,
) -> ApiLogService:
    return get_apilog_service(nestjs_client, api_log_mapper)


def provide_graph_search_service() -> GraphSearchService:
    return get_graph_search_service()


def provide_user_service(
    spring_client: SpringClientDep,
    nestjs_client: NestjsClientDep,
    user_mapper: UserMapperDep,
) -> UserService:
    return get_user_service(spring_client, nestjs_client, user_mapper)


def provide_vector_search_service(rag_tools: RAGToolsDep) -> VectorSearchService:
    return get_vector_search_service(rag_tools)


AlgorithmServiceDep = Annotated[AlgorithmService, Depends(provide_algorithm_service)]
AnalyzeServiceDep = Annotated[AnalyzeService, Depends(provide_analyze_service)]
GenerateServiceDep = Annotated[GenerateService, Depends(provide_generate_service)]
AiHistoryServiceDep = Annotated[AiHistoryService, Depends(provide_ai_history_service)]
ApiLogServiceDep = Annotated[ApiLogService, Depends(provide_api_log_service)]
GraphSearchServiceDep = Annotated[
    GraphSearchService, Depends(provide_graph_search_service)
]
UserServiceDep = Annotated[UserService, Depends(provide_user_service)]
VectorSearchServiceDep = Annotated[
    VectorSearchService, Depends(provide_vector_search_service)
]
