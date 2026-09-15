from typing import Annotated

from fastapi import Depends

from app.core.db import get_clickhouse_session_factory
from app.internal.crud import (
    AiHistoryMapper,
    ApiLogMapper,
    ArticleMapper,
    UserMapper,
    get_ai_history_mapper,
    get_api_log_mapper,
    get_article_mapper,
    get_user_mapper,
)

from .database import ClickHouseSessionFactoryDep


def provide_api_log_mapper(
    session_factory: ClickHouseSessionFactoryDep,
) -> ApiLogMapper:
    return get_api_log_mapper(session_factory)


def provide_article_mapper(
    session_factory: ClickHouseSessionFactoryDep,
) -> ArticleMapper:
    return get_article_mapper(session_factory)


def provide_user_mapper(
    session_factory: ClickHouseSessionFactoryDep,
) -> UserMapper:
    return get_user_mapper(session_factory)


def resolve_article_mapper() -> ArticleMapper:
    """在调度器等非请求链路中解析文章数仓 Mapper"""
    return get_article_mapper(get_clickhouse_session_factory())


AiHistoryMapperDep = Annotated[AiHistoryMapper, Depends(get_ai_history_mapper)]
ApiLogMapperDep = Annotated[ApiLogMapper, Depends(provide_api_log_mapper)]
ArticleMapperDep = Annotated[ArticleMapper, Depends(provide_article_mapper)]
UserMapperDep = Annotated[UserMapper, Depends(provide_user_mapper)]
