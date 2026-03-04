from collections.abc import Generator
from typing import Any, Optional

from app.db import get_db, get_redis_client


def get_db_dep() -> Generator[Any, None, None]:
    """获取数据库会话依赖
    
    Returns:
        Generator: 数据库会话生成器
    """
    return get_db()


def get_redis_dep() -> Optional[Any]:
    """获取 Redis 客户端依赖
    
    Returns:
        Optional[Any]: Redis 客户端实例或 None
    """
    return get_redis_client()
