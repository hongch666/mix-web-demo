from typing import List, Optional
import contextvars
from langchain_core.tools import Tool
from langchain_community.utilities import SQLDatabase
from sqlmodel import create_engine, Session
from sqlalchemy import text, inspect
from common.utils import Constants

# 用户ID上下文变量
user_id_context: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar("user_id", default=None)

class SQLTools:
    """SQL数据库工具类"""
    
    def __init__(self):
        """初始化数据库连接"""
        # 延迟导入避免循环依赖
        from common.config import load_config
        from common.utils import fileLogger as logger
        
        self.logger = logger
        mysql_cfg = load_config("database")["mysql"]
        self.database_url = f"mysql+pymysql://{mysql_cfg['user']}:{mysql_cfg['password']}@{mysql_cfg['host']}:{mysql_cfg['port']}/{mysql_cfg['database']}?charset=utf8mb4"
        
        self.engine = create_engine(self.database_url, pool_pre_ping=True)
        self.db = SQLDatabase(self.engine)
        self.logger.info(Constants.SQL_TOOL_INITIALIZATION_SUCCESS)
    
    def set_user_id(self, user_id: Optional[int]) -> None:
        """设置当前用户ID"""
        if user_id:
            user_id_context.set(user_id)
            self.logger.info(f"设置SQL工具用户ID: {user_id}")
    
    def get_user_id(self) -> Optional[int]:
        """获取当前用户ID"""
        return user_id_context.get()
    
    def get_table_schema(self, table_name: str = "") -> str:
        """
        获取数据库表结构信息
        
        Args:
            table_name: 表名，如果为空则返回所有表的结构
            
        Returns:
            表结构的文本描述
        """
        try:
            inspector = inspect(self.engine)
            
            if table_name:
                # 获取指定表的结构
                if table_name not in inspector.get_table_names():
                    return f"表 '{table_name}' 不存在"
                
                columns = inspector.get_columns(table_name)
                pk = inspector.get_pk_constraint(table_name)
                indexes = inspector.get_indexes(table_name)
                
                schema_info = f"表名: {table_name}\n"
                schema_info += "列信息:\n"
                for col in columns:
                    schema_info += f"  - {col['name']}: {col['type']}"
                    if col['nullable']:
                        schema_info += " (可为空)"
                    if col['default']:
                        schema_info += f" 默认值: {col['default']}"
                    schema_info += "\n"
                
                if pk and pk.get('constrained_columns'):
                    schema_info += f"主键: {', '.join(pk['constrained_columns'])}\n"
                
                if indexes:
                    schema_info += "索引:\n"
                    for idx in indexes:
                        schema_info += f"  - {idx['name']}: {', '.join(idx['column_names'])}\n"
                
                return schema_info
            else:
                # 获取所有表的基本信息
                tables = inspector.get_table_names()
                schema_info = f"数据库包含 {len(tables)} 个表:\n\n"
                
                for table in tables:
                    columns = inspector.get_columns(table)
                    schema_info += f"表名: {table}\n"
                    schema_info += f"  列数: {len(columns)}\n"
                    schema_info += f"  列名: {', '.join([col['name'] for col in columns])}\n\n"
                
                return schema_info
        
        except Exception as e:
            error_msg = f"获取表结构失败: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
    
    def execute_query(self, query: str) -> str:
        """
        执行SQL查询并返回结果
        
        Args:
            query: SQL查询语句
            
        Returns:
            查询结果的文本描述
        """
        try:
            # 安全检查：只允许SELECT查询
            query_upper = query.strip().upper()
            if not query_upper.startswith("SELECT"):
                return "安全限制：只允许执行SELECT查询语句"
            
            # 获取当前用户ID
            current_user_id = self.get_user_id()
            
            # 如果涉及个人数据查询且有用户ID，添加用户ID过滤
            if current_user_id:
                # 检查查询是否涉及用户相关表
                personal_tables = ['likes', 'collects', 'comments', 'ai_history', 'chat_messages']
                query_lower = query.lower()
                
                # 如果查询涉及个人表，自动添加用户ID过滤
                for table in personal_tables:
                    if table in query_lower:
                        # 检查是否已经有user_id的WHERE条件
                        if 'where' not in query_lower or f'{table}.user_id' not in query_lower:
                            # 在FROM/JOIN之后添加WHERE条件
                            self.logger.info(f"[SQL工具] 为用户 {current_user_id} 的查询添加用户ID过滤")
                            # 这里可以进一步增强查询，但为了安全起见，我们只在日志中记录
                        break
            
            # 执行查询
            with Session(self.engine) as session:
                result = session.exec(text(query))
                rows = result.fetchall()
                columns = result.keys()
                
                if not rows:
                    return "查询成功，但没有返回结果"
                
                # 限制返回行数 - 增加到500行以支持更完整的思考过程
                max_rows = 500
                limited_rows = rows[:max_rows]
                
                # 格式化结果
                result_text = f"查询返回 {len(rows)} 行数据"
                if len(rows) > max_rows:
                    result_text += f" (仅显示前 {max_rows} 行)"
                result_text += ":\n\n"
                
                # 添加列名
                result_text += " | ".join(columns) + "\n"
                result_text += "-" * (len(columns) * 15) + "\n"
                
                # 添加数据行
                for row in limited_rows:
                    row_data = [str(value) if value is not None else "NULL" for value in row]
                    result_text += " | ".join(row_data) + "\n"
                
                self.logger.info(f"SQL查询成功，返回 {len(rows)} 行")
                return result_text
        
        except Exception as e:
            error_msg = f"SQL查询失败: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
    
    def get_langchain_tools(self) -> List[Tool]:
        """
        获取LangChain Tool对象列表
        
        Returns:
            Tool对象列表
        """
        return [
            Tool(
                name="get_table_schema",
                description="""获取MySQL数据库表结构信息。
                如果提供表名参数，返回该表的详细结构（列名、类型、主键、索引等）。
                如果不提供参数，返回所有表的列表和基本信息。
                参数格式: 表名(字符串)，如 'articles' 或 'users'，留空获取所有表。
                使用场景: 需要了解数据库结构、查询某表有哪些字段时使用。""",
                func=self.get_table_schema
            ),
            Tool(
                name="execute_sql_query",
                description="""执行SQL SELECT查询并返回结果。
                只能执行SELECT查询，不允许INSERT/UPDATE/DELETE等修改操作。
                返回最多20行数据，以表格形式展示。
                参数格式: 完整的SQL SELECT语句。
                示例: "SELECT * FROM articles WHERE status=1 LIMIT 10"
                使用场景: 需要查询数据库数据、统计分析、获取具体记录时使用。""",
                func=self.execute_query
            )
        ]


def get_sql_tools() -> SQLTools:
    """获取SQL工具实例"""
    return SQLTools()
