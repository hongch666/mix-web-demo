from typing import Annotated

from fastapi import Depends

from app.internal.services import (
    AiHistoryService,
    AlgorithmService,
    AnalyzeService,
    ApiLogService,
    GeminiService,
    GenerateService,
    GlmService,
    GptService,
    GraphSearchService,
    UserService,
    VectorSearchService,
    get_ai_history_service,
    get_algorithm_service,
    get_analyze_service,
    get_apilog_service,
    get_gemini_service,
    get_generate_service,
    get_glm_service,
    get_gpt_service,
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
from .mappers import AiHistoryMapperDep, ArticleMapperDep, UserMapperDep


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


def provide_generate_service(
    glm_service: "GlmServiceDep",
    gemini_service: "GeminiServiceDep",
    gpt_service: "GptServiceDep",
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


def provide_api_log_service(nestjs_client: NestjsClientDep) -> ApiLogService:
    return get_apilog_service(nestjs_client)


def provide_graph_search_service() -> GraphSearchService:
    return get_graph_search_service()


def provide_user_service(
    spring_client: SpringClientDep,
    nestjs_client: NestjsClientDep,
    user_mapper: UserMapperDep,
) -> UserService:
    return get_user_service(spring_client, nestjs_client, user_mapper)


def provide_gpt_service(
    ai_history_mapper: AiHistoryMapperDep,
    spring_client: SpringClientDep,
) -> GptService:
    return get_gpt_service(ai_history_mapper, spring_client)


def provide_gemini_service(
    ai_history_mapper: AiHistoryMapperDep,
    spring_client: SpringClientDep,
) -> GeminiService:
    return get_gemini_service(ai_history_mapper, spring_client)


def provide_glm_service(
    ai_history_mapper: AiHistoryMapperDep,
    spring_client: SpringClientDep,
) -> GlmService:
    return get_glm_service(ai_history_mapper, spring_client)


def provide_vector_search_service() -> VectorSearchService:
    return get_vector_search_service()


AlgorithmServiceDep = Annotated[AlgorithmService, Depends(provide_algorithm_service)]
AnalyzeServiceDep = Annotated[AnalyzeService, Depends(provide_analyze_service)]
GenerateServiceDep = Annotated[GenerateService, Depends(provide_generate_service)]
AiHistoryServiceDep = Annotated[AiHistoryService, Depends(provide_ai_history_service)]
ApiLogServiceDep = Annotated[ApiLogService, Depends(provide_api_log_service)]
GraphSearchServiceDep = Annotated[
    GraphSearchService, Depends(provide_graph_search_service)
]
UserServiceDep = Annotated[UserService, Depends(provide_user_service)]
GptServiceDep = Annotated[GptService, Depends(provide_gpt_service)]
GeminiServiceDep = Annotated[GeminiService, Depends(provide_gemini_service)]
GlmServiceDep = Annotated[GlmService, Depends(provide_glm_service)]
VectorSearchServiceDep = Annotated[
    VectorSearchService, Depends(provide_vector_search_service)
]
