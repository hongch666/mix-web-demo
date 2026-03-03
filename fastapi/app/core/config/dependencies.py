from collections.abc import Generator

from app.db import get_db, get_redis_client


def get_db_dep() -> Generator:
    return get_db()


def get_redis_dep():
    return get_redis_client()
