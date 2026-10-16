from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import (
    AsyncSessionLocal,
    ClickHouseSessionFactory,
    get_clickhouse_db,
    get_clickhouse_session_factory,
    get_db,
)


def provide_db_session_factory() -> Callable[[], AsyncSession]:
    return AsyncSessionLocal


DbSession = Annotated[AsyncSession, Depends(get_db)]
DbSessionFactoryDep = Annotated[
    Callable[[], AsyncSession], Depends(provide_db_session_factory)
]
ClickHouseSession = Annotated[AsyncSession, Depends(get_clickhouse_db)]
ClickHouseSessionFactoryDep = Annotated[
    ClickHouseSessionFactory, Depends(get_clickhouse_session_factory)
]
