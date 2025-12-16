from sqlmodel import create_engine, Session, SQLModel
from typing import Generator, Optional, List
from config import load_config
from entity.po import Article, User, Category, SubCategory, AiHistory
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
        tables: 要创建的表名列表，如 ['ai_history', 'user']
                如果为 None，则创建所有表
    
    Examples:
        # 创建所有表
        create_tables()
        
        # 只创建 ai_history 表
        create_tables(['ai_history'])
        
        # 创建多个指定表
        create_tables(['ai_history', 'user', 'article'])
    """
    
    
    try:
        if tables is None:
            # 创建所有表
            SQLModel.metadata.create_all(engine)
            logger.info("数据库所有表初始化完成")
        else:
            # 只创建指定的表
            # 获取所有模型类的映射
            table_models = {
                'ai_history': AiHistory,
                'article': Article,
                'user': User,
                'category': Category,
                'sub_category': SubCategory,
            }
            
            # 筛选出需要创建的表
            tables_to_create = []
            for table_name in tables:
                if table_name in table_models:
                    model = table_models[table_name]
                    tables_to_create.append(model.__table__)
                else:
                    logger.warning(f"警告: 表名 '{table_name}' 不存在，跳过")
            
            if tables_to_create:
                # 创建指定的表
                SQLModel.metadata.create_all(engine, tables=tables_to_create)
                logger.info(f"数据库表初始化完成: {', '.join(tables)}")
            else:
                logger.error("没有找到需要创建的表")
    except Exception as e:
        logger.error(f"数据库表创建失败: {e}")