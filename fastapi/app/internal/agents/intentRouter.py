from typing import Any, Literal, Optional, Tuple

from app.core.base import Constants, Logger
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .tools.sqlTools import SQLTools, get_sql_tools
from .userPermissionManager import UserPermissionManager

IntentType = Literal[
    "database_query",
    "article_search",
    "log_analysis",
    "knowledge_query",
    "general_chat",
]


class StructuredIntent(BaseModel):
    """结构化意图识别结果（优先使用，避免脆弱文本匹配）"""

    type: IntentType = Field(description="识别出的用户意图类型")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="意图识别的置信度",
    )


class IntentRouter:
    """意图识别路由器，支持权限检查

    优先使用 with_structured_output 结构化输出，不可用时降级为文本匹配。
    """

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

        # 文本匹配降级链（始终创建，作为降级方案）
        self.chain = self.intent_prompt | self.llm | StrOutputParser()

        # 优先使用结构化输出，不可用时降级为文本匹配
        try:
            self.structured_chain = self.intent_prompt | self.llm.with_structured_output(StructuredIntent)
            self._use_structured_output = True
            self.logger.info("意图路由器初始化成功：使用 with_structured_output 结构化模式")
        except Exception as e:
            self._use_structured_output = False
            self.logger.warning(f"with_structured_output 不可用，降级为文本匹配模式: {e}")

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
        """异步路由用户问题（优先使用结构化输出，降级为文本匹配）"""
        try:
            if self._use_structured_output:
                return await self._route_structured(question)
            else:
                return await self._route_text_match(question)
        except Exception as e:
            self.logger.error(f"意图识别失败: {e}, 默认使用 article_search")
            return "article_search"

    async def _route_structured(self, question: str) -> IntentType:
        """通过 with_structured_output 链识别意图"""
        try:
            result: StructuredIntent = await self.structured_chain.ainvoke(
                {"question": question}
            )
            self.logger.info(
                f"意图识别结果(结构化): {question} -> {result.type} (置信度: {result.confidence:.2f})"
            )
            return result.type
        except Exception as e:
            # 结构化输出失败，降级为文本匹配
            self.logger.warning(
                f"结构化意图识别失败，降级为文本匹配: {e}"
            )
            return await self._route_text_match(question)

    async def _route_text_match(self, question: str) -> IntentType:
        """通过文本匹配识别意图（降级方案）"""
        result: Any = await self.chain.ainvoke({"question": question})
        result_text: str = str(result).strip().lower()

        if "database" in result_text or "数据库" in result_text:
            intent: IntentType = "database_query"
        elif (
            "article" in result_text
            or "文章" in result_text
            or "search" in result_text
        ):
            intent = "article_search"
        elif "log" in result_text or "日志" in result_text or "活动" in result_text:
            intent = "log_analysis"
        elif (
            "knowledge" in result_text
            or "知识" in result_text
            or "图谱" in result_text
            or "推荐" in result_text
            or "关系" in result_text
        ):
            intent = "knowledge_query"
        elif (
            "general" in result_text
            or "chat" in result_text
            or "闲聊" in result_text
        ):
            intent = "general_chat"
        else:
            intent = "article_search"

        self.logger.info(f"意图识别结果(文本匹配): {question} -> {intent}")
        return intent

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

        perm_manager: UserPermissionManager = UserPermissionManager(self.user_mapper)

        if intent == "database_query":
            try:
                sql_tools: SQLTools = get_sql_tools()
                if sql_tools.is_dangerous_nl_request(question):
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

        if intent == "knowledge_query":
            return intent, True, ""

        if intent == "log_analysis":
            has_permission, msg = await perm_manager.can_access_mongodb_logs_async(
                self.user_id, self.db, question
            )
            if not has_permission:
                return intent, False, msg
            return intent, True, ""

        return intent, True, ""
