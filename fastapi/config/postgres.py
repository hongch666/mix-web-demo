from sqlmodel import create_engine, Session
from typing import Generator
from config import load_config
from common.utils import fileLogger as logger

# PostgreSQL 配置
try:
    pg_config = load_config("database").get("postgres", {})
    if pg_config:
        PG_DATABASE_URL = f"postgresql://{pg_config['user']}:{pg_config['password']}@{pg_config['host']}:{pg_config['port']}/{pg_config['database']}"
        
        pool_pre_ping: bool = pg_config.get("pool_pre_ping", True)
        pool_size: int = pg_config.get("pool_size", 10)
        max_overflow: int = pg_config.get("max_overflow", 20)
        echo: bool = pg_config.get("echo", False)
        
        # 创建引擎
        pg_engine = create_engine(
            PG_DATABASE_URL,
            pool_pre_ping=pool_pre_ping,
            pool_size=pool_size,
            max_overflow=max_overflow,
            echo=echo
        )
        
        logger.info("PostgreSQL 向量数据库连接初始化完成")
    else:
        pg_engine = None
        logger.warning("PostgreSQL 配置未找到，向量功能将不可用")
except Exception as e:
    pg_engine = None
    logger.warning(f"PostgreSQL 初始化失败: {e}，向量功能将不可用")


def get_pg_db() -> Generator[Session, None, None]:
    """获取 PostgreSQL 数据库会话"""
    if pg_engine is None:
        raise RuntimeError("PostgreSQL 未配置或初始化失败")
    
    with Session(pg_engine) as session:
        yield session
