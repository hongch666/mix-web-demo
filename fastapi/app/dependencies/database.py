from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_clickhouse_db, get_db

DbSession = Annotated[AsyncSession, Depends(get_db)]
ClickHouseSession = Annotated[AsyncSession, Depends(get_clickhouse_db)]
