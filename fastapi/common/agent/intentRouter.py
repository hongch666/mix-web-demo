from typing import Any, Literal, Optional, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlmodel import Session
from common.agent import UserPermissionManager
from common.utils import Constants

class IntentRouter:
    """意图识别路由器，支持权限检查"""
    
    def __init__(self, llm: Any, db: Optional[Session] = None, user_id: Optional[int] = None,
                 user_mapper: Optional[Any] = None) -> None:
        """
        初始化路由器
        
        Args:
            llm: LangChain LLM实例
            db: 数据库会话（用于权限检查）
            user_id: 当前用户ID（用于权限检查）
            user_mapper: 用户 Mapper 实例（用于权限检查）
        """
        # 延迟导入避免循环依赖
        from common.utils import fileLogger as logger
        self.logger = logger
        
        self.llm: Any = llm
        self.db: Optional[Session] = db
        self.user_id: Optional[int] = user_id
        self.user_mapper: Optional[Any] = user_mapper
        
        # 创建意图识别提示词
        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", Constants.ROUTER_INTENT_PROMPT),
            ("human", "用户问题：{question}")
        ])
        
        # 创建链
        self.chain = self.intent_prompt | self.llm | StrOutputParser()
    
    def set_user_context(self, user_id: int, db: Session) -> None:
        """
        设置用户上下文（用于权限检查）
        
        Args:
            user_id: 用户ID
            db: 数据库会话
        """
        self.user_id = user_id
        self.db = db
    
    def route(self, question: str) -> Literal["database_query", "article_search", "log_analysis", "general_chat"]:
        """
        路由用户问题
        
        Args:
            question: 用户问题
            
        Returns:
            意图类型：database_query、article_search、log_analysis 或 general_chat
        """
        try:
            result = self.chain.invoke({"question": question}).strip().lower()
            
            # 标准化结果
            if "database" in result or "数据库" in result:
                intent = "database_query"
            elif "article" in result or "文章" in result or "search" in result:
                intent = "article_search"
            elif "log" in result or "日志" in result or "活动" in result:
                intent = "log_analysis"
            elif "general" in result or "chat" in result or "闲聊" in result:
                intent = "general_chat"
            else:
                # 默认使用文章搜索
                intent = "article_search"
            
            self.logger.info(f"意图识别结果: {question} -> {intent}")
            return intent
            
        except Exception as e:
            self.logger.error(f"意图识别失败: {e}, 默认使用article_search")
            return "article_search"
    
    def route_with_permission_check(self, question: str, user_id: Optional[int] = None, db: Optional[Session] = None) -> Tuple[str, bool, str]:
        """
        路由用户问题并检查权限
        
        Args:
            question: 用户问题
            user_id: 用户ID（可选，如果提供则进行权限检查）
            db: 数据库会话（可选，如果提供则进行权限检查）
            
        Returns:
            (意图类型, 是否有权限, 错误信息)
            - 意图类型：database_query、article_search、log_analysis 或 general_chat
            - 是否有权限：True 如果用户有权限执行此操作
            - 错误信息：如果没有权限，包含错误信息；否则为空字符串
        """
        # 获取意图
        intent = self.route(question)
        
        # 如果提供了用户上下文，更新到实例中
        if user_id is not None and db is not None:
            self.user_id = user_id
            self.db = db
        
        # 如果没有用户上下文，只允许文章搜索和闲聊
        if not self.user_id or not self.db:
            if intent in ["database_query", "log_analysis"]:
                return intent, False, Constants.INTENT_ROUTER_NO_PERMISSION_ERROR
            return intent, True, ""
        
        # 检查权限
        perm_manager = UserPermissionManager(self.user_mapper)
        
        if intent == "database_query":
            has_permission, msg = perm_manager.can_access_sql_tools(self.user_id, self.db, question)
            if not has_permission:
                return intent, False, msg
            return intent, True, ""
        
        elif intent == "log_analysis":
            has_permission, msg = perm_manager.can_access_mongodb_logs(self.user_id, self.db, question)
            if not has_permission:
                return intent, False, msg
            return intent, True, ""
        
        else:
            # article_search 和 general_chat 对所有用户开放
            return intent, True, ""
