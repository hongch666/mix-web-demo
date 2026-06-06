from functools import lru_cache
from typing import Any, Dict

from app.core.base import Logger
from app.core.config import load_config


def get_postgres_config() -> Dict[str, Any]:
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
            f"PostgreSQL 连接字符串构建成功: {cfg['host']}:{cfg['port']}/{cfg['database']}"
        )
        return connection_string
    except Exception as e:
        Logger.error(f"PostgreSQL 连接字符串构建失败: {e}")
        raise
