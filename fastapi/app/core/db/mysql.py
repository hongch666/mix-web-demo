from collections.abc import AsyncGenerator
from contextlib import contextmanager
from typing import Generator, List, Optional
from urllib.parse import quote_plus

from app.core.base import Constants, Logger
from app.core.config import load_config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session as SASession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

Base = declarative_base()

server_config = load_config("server")
mysql_config = load_config("database")["mysql"]
SERVER_MODE: str = str(server_config.get("mode", "dev")).strip().lower()
HOST: str = mysql_config["host"]
PORT: int = mysql_config["port"]
DATABASE: str = mysql_config["database"]
USER: str = mysql_config["user"]
PASSWORD: str = str(mysql_config["password"])
ENCODED_PASSWORD: str = quote_plus(str(PASSWORD))

DATABASE_URL: str = f"mysql+pymysql://{USER}:{ENCODED_PASSWORD}@{HOST}:{PORT}/{DATABASE}?charset=utf8mb4"

POOL_SIZE: int = int(mysql_config.get("pool_size", 30))
MAX_OVERFLOW: int = int(mysql_config.get("max_overflow", 80))
POOL_RECYCLE: int = int(mysql_config.get("pool_recycle", 3600))
POOL_PRE_PING: bool = mysql_config.get("pool_pre_ping", True)
POOL_TIMEOUT: int = int(mysql_config.get("pool_timeout", 30))
READ_TIMEOUT: int = int(mysql_config.get("read_timeout", 10))
WRITE_TIMEOUT: int = int(mysql_config.get("write_timeout", 10))
AUTOCOMMIT: bool = mysql_config.get("autocommit", False)
ECHO: bool = SERVER_MODE == "dev"

# 配置连接池参数以支持高并发访问
engine = create_engine(
    DATABASE_URL,
    echo=ECHO,
    poolclass=QueuePool,
    pool_size=POOL_SIZE,  # 基础连接池大小
    max_overflow=MAX_OVERFLOW,  # 最多额外创建的连接数
    pool_recycle=POOL_RECYCLE,  # 连接回收时间（秒）
    pool_pre_ping=POOL_PRE_PING,  # 每次取连接前进行ping检查
    pool_timeout=POOL_TIMEOUT,  # 获取连接的超时时间（秒）
    connect_args={
        "read_timeout": READ_TIMEOUT,  # pymysql 读超时（秒）
        "write_timeout": WRITE_TIMEOUT,  # pymysql 写超时（秒）
        "autocommit": AUTOCOMMIT,
    },
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
    class_=SASession,
)


async def get_db() -> AsyncGenerator[SASession, None]:
    with SessionLocal() as session:
        yield session


def create_db_session() -> SASession:
    return SessionLocal()


@contextmanager
def get_db_sync() -> Generator[SASession, None, None]:
    with SessionLocal() as session:
        yield session


def create_tables(tables: Optional[List[str]] = None) -> None:
    """
    创建数据库表

    Args:
        tables: 要创建的表名列表，如 ['ai_history']
                只支持创建 ai_history 表，使用 SQL 直接创建以确保字段类型正确

    Examples:
        # 只创建 ai_history 表
        create_tables(['ai_history'])
    """

    try:
        if tables and "ai_history" in tables:
            # 使用 SQL 直接创建 ai_history 表，确保 TEXT 类型正确
            connection = engine.raw_connection()
            cursor = connection.cursor()
            try:
                # 检查表是否已存在
                check_sql = Constants.AI_CHAT_SQL_TABLE_EXISTENCE_CHECK
                cursor.execute(check_sql, (DATABASE,))
                table_exists = cursor.fetchone() is not None

                if not table_exists:
                    create_sql = Constants.AI_CHAT_SQL_TABLE_CREATION_MESSAGE
                    cursor.execute(create_sql)
                    connection.commit()
                    Logger.info(Constants.AI_CHAT_TABLE_CREATION_MESSAGE)
                else:
                    Logger.info(Constants.AI_CHAT_TABLE_EXISTS_MESSAGE)
            finally:
                cursor.close()
                connection.close()
        else:
            Logger.warning(Constants.AI_CHAT_TABLE_UNSUPPORTED_MESSAGE)
    except Exception as e:
        Logger.error(f"数据库表创建失败: {e}")
        import traceback

        Logger.error(traceback.format_exc())
