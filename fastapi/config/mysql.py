from sqlmodel import create_engine, Session
from typing import Generator, Optional, List
from config import load_config
from common.utils import fileLogger as logger

HOST: str = load_config("database")["mysql"]["host"]
PORT: int = load_config("database")["mysql"]["port"]
DATABASE: str = load_config("database")["mysql"]["database"]
USER: str = load_config("database")["mysql"]["user"]
PASSWORD: str = load_config("database")["mysql"]["password"]

DATABASE_URL: str = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?charset=utf8mb4"
engine = create_engine(DATABASE_URL, echo=True)

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
                check_sql = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'ai_history'"
                cursor.execute(check_sql, (DATABASE,))
                table_exists = cursor.fetchone() is not None
                
                if not table_exists:
                    create_sql = """
                    CREATE TABLE `ai_history` (
                        `id` BIGINT NOT NULL AUTO_INCREMENT,
                        `user_id` BIGINT,
                        `ask` TEXT NOT NULL,
                        `reply` TEXT NOT NULL,
                        `thinking` TEXT,
                        `ai_type` VARCHAR(30),
                        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        PRIMARY KEY (`id`),
                        KEY `idx_user_id` (`user_id`)
                    ) COMMENT='AI聊天记录' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    """
                    cursor.execute(create_sql)
                    connection.commit()
                    logger.info("ai_history 表创建完成 (TEXT类型)")
                else:
                    logger.info("ai_history 表已存在")
            finally:
                cursor.close()
                connection.close()
        else:
            logger.warning("仅支持创建 ai_history 表")
    except Exception as e:
        logger.error(f"数据库表创建失败: {e}")
        import traceback
        logger.error(traceback.format_exc())