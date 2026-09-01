from typing import Any, Literal, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.base import Logger
from app.core.constants import Messages, Prompts

from .userPermissionManager import UserPermissionManager

IntentType = Literal[
    "database_query",
    "article_search",
    "log_analysis",
    "knowledge_query",
    "general_chat",
]

IntentResolution = Literal[
    "structured",
    "text_fallback",
    "default_fallback",
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
        use_structured_output: bool = True,
    ) -> None:
        """
        初始化路由器

        Args:
            llm: LangChain LLM实例
            db: 数据库会话（用于权限检查）
            user_id: 当前用户ID（用于权限检查）
        """

        self.logger = Logger

        self.llm: Any = llm
        self.db: Optional[Session] = db
        self.user_id: Optional[int] = user_id
        self._use_structured_output = use_structured_output

        # 创建意图识别提示词
        self.intent_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", Prompts.ROUTER_INTENT_PROMPT),
                ("human", "用户问题：{question}"),
            ]
        )

        # 文本匹配降级链（始终创建，作为降级方案）
        self.chain = self.intent_prompt | self.llm | StrOutputParser()

        # 优先使用结构化输出，不可用时降级为文本匹配
        if self._use_structured_output:
            try:
                self.structured_chain = (
                    self.intent_prompt
                    | self.llm.with_structured_output(StructuredIntent)
                )
                self.logger.info(Messages.INTENT_ROUTER_STRUCTURED_OUTPUT_READY)
            except Exception as e:
                self._use_structured_output = False
                self.logger.warning(Messages.INTENT_STRUCTURED_OUTPUT_UNAVAILABLE(e))

    def set_user_context(self, user_id: int, db: Session) -> None:
        """
        设置用户上下文（用于权限检查）

        Args:
            user_id: 用户ID
            db: 数据库会话
        """
        self.user_id = user_id
        self.db = db

    async def route_async(
        self, question: str, runnable_config: Optional[dict] = None
    ) -> tuple[IntentType, IntentResolution]:
        """异步路由用户问题（优先使用结构化输出，降级为文本匹配）

        Args:
            question: 用户问题
            runnable_config: LangChain RunnableConfig (用于 LangSmith 追踪)

        Returns:
            (意图类型, 识别路径)
        """
        config = dict(runnable_config) if runnable_config else {}
        config.setdefault("run_name", "intent.route")
        try:
            if self._use_structured_output:
                intent, resolution = await self._route_structured(question, config)
            else:
                intent, resolution = await self._route_text_match(question, config)
            return intent, resolution
        except Exception as e:
            self.logger.error(Messages.INTENT_RECOGNITION_FAILED(e))
            return "article_search", "default_fallback"

    async def _route_structured(
        self, question: str, config: dict
    ) -> tuple[IntentType, IntentResolution]:
        """通过 with_structured_output 链识别意图"""
        try:
            result: Any = await self.structured_chain.ainvoke(
                {"question": question}, config=config
            )
            if isinstance(result, str):
                return self._resolve_text_intent(result), "text_fallback"
            self.logger.info(
                Messages.INTENT_STRUCTURED_RESULT(
                    question, result.type, result.confidence
                )
            )
            return result.type, "structured"
        except Exception as e:
            # 结构化输出失败，降级为文本匹配
            self.logger.warning(Messages.INTENT_STRUCTURED_FALLBACK(e))
            return await self._route_text_match(question, config)

    async def _route_text_match(
        self, question: str, config: dict
    ) -> tuple[IntentType, IntentResolution]:
        """通过文本匹配识别意图（降级方案）"""
        result: Any = await self.chain.ainvoke({"question": question}, config=config)
        result_text: str = str(result).strip().lower()

        intent = self._resolve_text_intent(result_text)

        self.logger.info(Messages.INTENT_TEXT_RESULT(question, intent))
        return intent, "text_fallback"

    @staticmethod
    def _resolve_text_intent(result_text: str) -> IntentType:
        """将模型返回的意图文本转换为系统支持的意图类型"""
        normalized_text = result_text.strip().lower()

        if "database" in normalized_text or "数据库" in normalized_text:
            return "database_query"
        elif (
            "article" in normalized_text
            or "文章" in normalized_text
            or "search" in normalized_text
        ):
            return "article_search"
        elif (
            "log" in normalized_text
            or "日志" in normalized_text
            or "活动" in normalized_text
        ):
            return "log_analysis"
        elif (
            "knowledge" in normalized_text
            or "知识" in normalized_text
            or "图谱" in normalized_text
            or "推荐" in normalized_text
            or "关系" in normalized_text
        ):
            return "knowledge_query"
        elif (
            "general" in normalized_text
            or "chat" in normalized_text
            or "闲聊" in normalized_text
        ):
            return "general_chat"
        return "article_search"

    async def route_with_permission_check_async(
        self,
        question: str,
        user_id: Optional[int] = None,
        db: Optional[Session] = None,
        runnable_config: Optional[dict] = None,
    ) -> tuple[IntentType, bool, str, IntentResolution]:
        """异步路由用户问题并检查权限

        Returns:
            (意图类型, 是否有权限, 权限消息, 识别路径)
        """
        intent, resolution = await self.route_async(question, runnable_config)

        if user_id is not None and db is not None:
            self.user_id = user_id
            self.db = db

        if not self.user_id or not self.db:
            if intent in ["database_query", "log_analysis"]:
                return (
                    intent,
                    False,
                    Messages.INTENT_ROUTER_NO_PERMISSION_ERROR,
                    resolution,
                )
            return intent, True, "", resolution

        perm_manager: UserPermissionManager = UserPermissionManager()

        if intent == "database_query":
            try:
                if Messages.is_dangerous_nl_request(question):
                    self.logger.warning(Messages.INTENT_WRITE_SQL_BLOCKED(question))
                    return (
                        intent,
                        False,
                        Messages.SQL_NATURAL_LANGUAGE_WRITE_BLOCK_MESSAGE,
                        resolution,
                    )
            except Exception as e:
                self.logger.warning(Messages.INTENT_WRITE_CHECK_FAILED(e))

            has_permission, msg = await perm_manager.can_access_sql_tools_async(
                self.user_id, self.db, question
            )
            if not has_permission:
                return intent, False, msg, resolution
            return intent, True, "", resolution

        if intent == "knowledge_query":
            return intent, True, "", resolution

        if intent == "log_analysis":
            has_permission, msg = await perm_manager.can_access_mongodb_logs_async(
                self.user_id, self.db, question
            )
            if not has_permission:
                return intent, False, msg, resolution
            return intent, True, "", resolution

        return intent, True, "", resolution
