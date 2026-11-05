import asyncio
from functools import lru_cache
from typing import Any

import psycopg2

from app.core.base import Logger
from app.core.config import load_config
from app.core.constants import Messages, PostgreSQLIndexes


def get_postgres_config() -> dict[str, Any]:
    """获取 PostgreSQL 配置"""
    return load_config("database")["postgres"]


@lru_cache
def get_pgvector_connection_string() -> str:
    """
    获取 PostgreSQL 向量存储连接字符串（LangChain PGVector 使用）

    Returns:
        psycopg2 格式连接字符串: postgresql+psycopg2://user:password@host:port/database
    """
    try:
        cfg = get_postgres_config()
        connection_string = (
            f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}"
            f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
        )
        Logger.info(
            Messages.POSTGRES_CONNECTION_STRING_CREATED(
                cfg["host"], cfg["port"], cfg["database"]
            )
        )
        return connection_string
    except Exception as e:
        Logger.error(Messages.POSTGRES_CONNECTION_STRING_CREATE_FAILED(e))
        raise


async def ensure_pgvector_indexes_async() -> None:
    """启用 pgvector 扩展并为向量表补齐 ANN 与表达式索引

    向量表由 LangChain PGVector 在首次写入时创建，首次启动时可能还不存在，
    此时只启用扩展并跳过索引，等下次启动或表建好后自动补齐
    """

    await asyncio.to_thread(_ensure_pgvector_indexes_sync)


def _ensure_pgvector_indexes_sync() -> None:
    """同步执行 pgvector 的扩展与索引 DDL，由异步入口放入线程池调用"""

    cfg: dict[str, Any] = get_postgres_config()
    try:
        connection = psycopg2.connect(
            host=cfg["host"],
            port=cfg["port"],
            dbname=cfg["database"],
            user=cfg["user"],
            password=cfg["password"],
            connect_timeout=5,
        )
    except Exception as e:
        Logger.error(Messages.PGVECTOR_INDEX_INITIALIZATION_FAILED(e))
        return

    try:
        # DDL 自带 IF NOT EXISTS，autocommit 避免长事务持有锁
        connection.autocommit = True
        with connection.cursor() as cursor:
            try:
                cursor.execute(PostgreSQLIndexes.EXTENSION)
            except Exception as e:
                Logger.warning(Messages.PGVECTOR_INDEX_INITIALIZATION_FAILED(e))

            cursor.execute(
                "SELECT to_regclass(%s)", (PostgreSQLIndexes.EMBEDDING_TABLE,)
            )
            table_row = cursor.fetchone()
            if not table_row or table_row[0] is None:
                Logger.info(Messages.PGVECTOR_EMBEDDING_TABLE_MISSING)
                return

            # LangChain 建表时 embedding 是无限定的 vector，而 pgvector 的 ANN 索引要求固定维度，
            # 因此先按已有数据的实际维度补齐列类型，否则建索引会报 column does not have dimensions
            cursor.execute(PostgreSQLIndexes.COLUMN_TYPE)
            column_type_row = cursor.fetchone()
            column_type: str = (column_type_row[0] if column_type_row else "") or ""
            if "(" not in column_type:
                cursor.execute(PostgreSQLIndexes.VECTOR_DIMS)
                dims_row = cursor.fetchone()
                if not dims_row or not dims_row[0]:
                    Logger.info(Messages.PGVECTOR_EMBEDDING_EMPTY)
                    return
                dims = int(dims_row[0])
                cursor.execute(PostgreSQLIndexes.SET_DIMENSIONS.format(dims=dims))
                Logger.info(Messages.PGVECTOR_DIMENSIONS_ASSIGNED(dims))

            try:
                cursor.execute(PostgreSQLIndexes.HNSW)
            except Exception:
                # pgvector < 0.5 不支持 HNSW，降级到 IVFFlat
                Logger.warning(Messages.PGVECTOR_HNSW_UNSUPPORTED)
                cursor.execute(PostgreSQLIndexes.IVFFLAT)

            cursor.execute(PostgreSQLIndexes.ARTICLE_ID)
        Logger.info(Messages.PGVECTOR_INDEX_INITIALIZATION_SUCCESS)
    except Exception as e:
        Logger.error(Messages.PGVECTOR_INDEX_INITIALIZATION_FAILED(e))
    finally:
        connection.close()
