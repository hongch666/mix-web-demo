from typing import Annotated

from fastapi import Depends

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

AiHistoryMapperDep = Annotated[AiHistoryMapper, Depends(get_ai_history_mapper)]
ApiLogMapperDep = Annotated[ApiLogMapper, Depends(get_api_log_mapper)]
ArticleMapperDep = Annotated[ArticleMapper, Depends(get_article_mapper)]
UserMapperDep = Annotated[UserMapper, Depends(get_user_mapper)]
