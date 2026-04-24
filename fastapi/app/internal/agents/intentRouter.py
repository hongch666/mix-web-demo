from typing import Any, Literal, Optional, Tuple

from app.core.base import Constants
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy.orm import Session

from .tools.sqlTools import get_sql_tools
from .userPermissionManager import UserPermissionManager

IntentType = Literal["database_query", "article_search", "log_analysis", "general_chat"]


class IntentRouter:
    """意图识别路由器，支持权限检查"""

    def __init__(
        self,
        llm: Any,
        db: Optional[Session] = None,
        user_id: Optional[int] = None,
        user_mapper: Optional[Any] = None,
    ) -> None:
        """
        初始化路由器

        Args:
            llm: LangChain LLM实例
            db: 数据库会话（用于权限检查）
            user_id: 当前用户ID（用于权限检查）
            user_mapper: 用户 Mapper 实例（用于权限检查）
        """
        # 延迟导入避免循环依赖
        from app.core.base import Logger

        self.logger = Logger

        self.llm: Any = llm
        self.db: Optional[Session] = db
        self.user_id: Optional[int] = user_id
        self.user_mapper: Optional[Any] = user_mapper

        # 创建意图识别提示词
        self.intent_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", Constants.ROUTER_INTENT_PROMPT),
                ("human", "用户问题：{question}"),
            ]
        )

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

    async def route_async(self, question: str) -> IntentType:
        """异步路由用户问题"""
        try:
            result = await self.chain.ainvoke({"question": question})
            result_text = str(result).strip().lower()

            if "database" in result_text or "数据库" in result_text:
                intent = "database_query"
            elif (
                "article" in result_text
                or "文章" in result_text
                or "search" in result_text
            ):
                intent = "article_search"
            elif "log" in result_text or "日志" in result_text or "活动" in result_text:
                intent = "log_analysis"
            elif (
                "general" in result_text
                or "chat" in result_text
                or "闲聊" in result_text
            ):
                intent = "general_chat"
            else:
                intent = "article_search"

            self.logger.info(f"意图识别结果: {question} -> {intent}")
            return intent
        except Exception as e:
            self.logger.error(f"意图识别失败: {e}, 默认使用article_search")
            return "article_search"

    async def route_with_permission_check_async(
        self, question: str, user_id: Optional[int] = None, db: Optional[Session] = None
    ) -> Tuple[IntentType, bool, str]:
        """异步路由用户问题并检查权限"""
        intent = await self.route_async(question)

        if user_id is not None and db is not None:
            self.user_id = user_id
            self.db = db

        if not self.user_id or not self.db:
            if intent in ["database_query", "log_analysis"]:
                return intent, False, Constants.INTENT_ROUTER_NO_PERMISSION_ERROR
            return intent, True, ""

        perm_manager = UserPermissionManager(self.user_mapper)

        if intent == "database_query":
            try:
                sql_tools = get_sql_tools()
                if await sql_tools.is_dangerous_nl_request(question):
                    self.logger.warning(f"拦截疑似写操作SQL请求: {question}")
                    return (
                        intent,
                        False,
                        Constants.SQL_NATURAL_LANGUAGE_WRITE_BLOCK_MESSAGE,
                    )
            except Exception as e:
                self.logger.warning(f"写操作意图检测失败，继续执行权限校验: {e}")

            has_permission, msg = await perm_manager.can_access_sql_tools_async(
                self.user_id, self.db, question
            )
            if not has_permission:
                return intent, False, msg
            return intent, True, ""

        if intent == "log_analysis":
            has_permission, msg = await perm_manager.can_access_mongodb_logs_async(
                self.user_id, self.db, question
            )
            if not has_permission:
                return intent, False, msg
            return intent, True, ""

        return intent, True, ""
