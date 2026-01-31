from sqlmodel import create_engine, Session
from sqlalchemy.pool import QueuePool
from typing import Generator, Optional, List
from config import load_config
from common.utils import fileLogger as logger, Constants

HOST: str = load_config("database")["mysql"]["host"]
PORT: int = load_config("database")["mysql"]["port"]
DATABASE: str = load_config("database")["mysql"]["database"]
USER: str = load_config("database")["mysql"]["user"]
PASSWORD: str = load_config("database")["mysql"]["password"]

DATABASE_URL: str = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?charset=utf8mb4"

# 从配置文件读取连接池参数
mysql_config = load_config("database")["mysql"]
POOL_SIZE: int = int(mysql_config.get("pool_size", 30))
MAX_OVERFLOW: int = int(mysql_config.get("max_overflow", 80))
POOL_RECYCLE: int = int(mysql_config.get("pool_recycle", 3600))
POOL_PRE_PING: bool = mysql_config.get("pool_pre_ping", True)
POOL_TIMEOUT: int = int(mysql_config.get("pool_timeout", 30))
READ_TIMEOUT: int = int(mysql_config.get("read_timeout", 10))
WRITE_TIMEOUT: int = int(mysql_config.get("write_timeout", 10))
AUTOCOMMIT: bool = mysql_config.get("autocommit", False)
ECHO: bool = mysql_config.get("echo", False)

# 配置连接池参数以支持高并发访问
engine = create_engine(
    DATABASE_URL, 
    echo=ECHO,
    poolclass=QueuePool,
    pool_size=POOL_SIZE,                    # 基础连接池大小
    max_overflow=MAX_OVERFLOW,              # 最多额外创建的连接数
    pool_recycle=POOL_RECYCLE,              # 连接回收时间（秒）
    pool_pre_ping=POOL_PRE_PING,            # 每次取连接前进行ping检查
    pool_timeout=POOL_TIMEOUT,              # 获取连接的超时时间（秒）
    connect_args={
        "read_timeout": READ_TIMEOUT,       # pymysql 读超时（秒）
        "write_timeout": WRITE_TIMEOUT,     # pymysql 写超时（秒）
        "autocommit": AUTOCOMMIT
    }
)

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

def create_tables(tables: Optional[List[str]] = None):
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
        if tables and 'ai_history' in tables:
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
                    logger.info(Constants.AI_CHAT_TABLE_CREATION_MESSAGE)
                else:
                    logger.info(Constants.AI_CHAT_TABLE_EXISTS_MESSAGE)
            finally:
                cursor.close()
                connection.close()
        else:
            logger.warning(Constants.AI_CHAT_TABLE_UNSUPPORTED_MESSAGE)
    except Exception as e:
        logger.error(f"数据库表创建失败: {e}")
        import traceback
        logger.error(traceback.format_exc())