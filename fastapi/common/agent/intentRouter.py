from typing import Literal, Optional, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlmodel import Session
from common.agent.userPermissionManager import UserPermissionManager

class IntentRouter:
    """意图识别路由器，支持权限检查"""
    
    def __init__(self, llm, db: Optional[Session] = None, user_id: Optional[int] = None, 
                 user_mapper=None):
        """
        初始化路由器
        
        Args:
            llm: LangChain LLM实例
            db: 数据库会话（用于权限检查）
            user_id: 当前用户ID（用于权限检查）
            user_mapper: 用户 Mapper 实例（用于权限检查）
        """
        # 延迟导入避免循环依赖
        from common.utils import fileLogger
        self.logger = fileLogger
        
        self.llm = llm
        self.db = db
        self.user_id = user_id
        self.user_mapper = user_mapper
        
        # 创建意图识别提示词
        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个智能路由助手，需要判断用户的问题类型。

            分析用户问题，判断应该使用哪种方式处理：

            1. **database_query** - 需要查询数据库统计数据、获取记录列表、数据分析时选择
            - 关键词：多少、统计、列表、查询、总数、排行、最新、用户信息等
            - 示例：
                * "有多少篇文章？"
                * "最近发布的10篇文章"
                * "user_id为123的用户信息"
                * "各分类的文章数量统计"
                * "浏览量最高的文章"

            2. **article_search** - 需要搜索文章内容、技术知识、教程等时选择
            - 关键词：如何、怎么做、教程、学习、介绍、什么是、原理等
            - 示例：
                * "如何使用Python进行数据分析？"
                * "React Hooks的使用方法"
                * "什么是机器学习？"
                * "Docker容器化部署教程"
                * "数据库索引的原理"

            3. **log_analysis** - 需要查询系统日志、API日志、用户活动分析时选择
            - 关键词：日志、活动、请求记录、错误、追踪、统计访问等
            - 示例：
                * "最近的错误日志"
                * "用户活动统计"
                * "API请求记录"
                * "今天有哪些错误"

            4. **general_chat** - 简单问候、闲聊、不需要查询数据的问题
            - 示例：
                * "你好"
                * "今天天气怎么样"
                * "你能做什么"

            请只返回以下四个选项之一：database_query、article_search、log_analysis、general_chat"""),
            ("human", "用户问题：{question}")
        ])
        
        # 创建链
        self.chain = self.intent_prompt | self.llm | StrOutputParser()
    
    def set_user_context(self, user_id: int, db: Session):
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
    
    def route_with_permission_check(self, question: str, user_id: Optional[int] = None, 
                                    db: Optional[Session] = None) -> Tuple[str, bool, str]:
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
                return intent, False, "权限拒绝：此功能需要登录后才能使用。请先登录您的账户。您可以继续使用文章搜索和闲聊功能。"
            return intent, True, ""
        
        # 检查权限
        perm_manager = UserPermissionManager(self.user_mapper)
        
        if intent == "database_query":
            has_permission, msg = perm_manager.can_access_sql_tools(self.user_id, self.db)
            if not has_permission:
                return intent, False, msg
            return intent, True, ""
        
        elif intent == "log_analysis":
            has_permission, msg = perm_manager.can_access_mongodb_logs(self.user_id, self.db)
            if not has_permission:
                return intent, False, msg
            return intent, True, ""
        
        else:
            # article_search 和 general_chat 对所有用户开放
            return intent, True, ""
