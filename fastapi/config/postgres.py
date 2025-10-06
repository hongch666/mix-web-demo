from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from config import load_config
from common.utils import fileLogger as logger

# PostgreSQL 配置
try:
    pg_config = load_config("database").get("postgres", {})
    if pg_config:
        PG_DATABASE_URL = f"postgresql://{pg_config['user']}:{pg_config['password']}@{pg_config['host']}:{pg_config['port']}/{pg_config['database']}"
        
        # 创建引擎
        pg_engine = create_engine(
            PG_DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=False
        )
        
        PgSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)
        
        logger.info("PostgreSQL 向量数据库连接初始化完成")
    else:
        pg_engine = None
        PgSessionLocal = None
        logger.warning("PostgreSQL 配置未找到，向量功能将不可用")
except Exception as e:
    pg_engine = None
    PgSessionLocal = None
    logger.warning(f"PostgreSQL 初始化失败: {e}，向量功能将不可用")


def get_pg_db() -> Generator[Session, None, None]:
    """获取 PostgreSQL 数据库会话"""
    if PgSessionLocal is None:
        raise RuntimeError("PostgreSQL 未配置或初始化失败")
    
    db = PgSessionLocal()
    try:
        yield db
    finally:
        db.close()
