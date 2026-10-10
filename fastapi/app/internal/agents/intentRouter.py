import re
from collections.abc import Sequence
from typing import Any, Optional, cast

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.base import Logger
from app.core.constants import (
    IntentConstants,
    IntentExpression,
    IntentResolution,
    IntentType,
    Messages,
    Prompts,
)

from .userPermissionManager import UserPermissionManager, get_user_permission_manager


def _build_marker_pattern(marker: str) -> re.Pattern[str]:
    """编译关键词正则：纯 ASCII 关键词按词边界匹配，中文关键词按子串匹配"""
    if marker.isascii():
        return re.compile(
            rf"(?<![a-z0-9]){re.escape(marker)}(?![a-z0-9])", re.IGNORECASE
        )
    return re.compile(re.escape(marker))


# 关键词表在导入时编译一次，文本降级链路按表顺序匹配（表顺序即优先级）
_INTENT_MARKER_PATTERNS: tuple[tuple[IntentType, tuple[re.Pattern[str], ...]], ...] = (
    cast(
        "tuple[tuple[IntentType, tuple[re.Pattern[str], ...]], ...]",
        tuple(
            (intent, tuple(_build_marker_pattern(marker) for marker in markers))
            for intent, markers in IntentConstants.MARKERS
        ),
    )
)


def format_intent_expression(intents: Sequence[str]) -> IntentExpression:
    """把意图列表格式化为表达式，去重并剔除不支持的意图"""
    valid = [
        item
        for item in dict.fromkeys(intents)
        if item in IntentConstants.SUPPORTED_TYPES
    ]
    return "|".join(valid) if valid else IntentConstants.DEFAULT


def parse_intent_expression(expression: IntentExpression) -> list[IntentType]:
    """解析意图表达式为意图列表，过滤未知值并在空结果时回落默认意图"""
    intents: list[IntentType] = [
        cast(IntentType, item)
        for item in dict.fromkeys(str(expression).split("|"))
        if item in IntentConstants.SUPPORTED_TYPES
    ]
    if not intents:
        return [IntentConstants.DEFAULT]
    return intents


def normalize_intents(intents: Sequence[str]) -> list[IntentType]:
    """规范化模型给出的意图集合：去重、过滤未知值、剔除与其它领域并存的闲聊"""
    unique: list[IntentType] = [
        cast(IntentType, item)
        for item in dict.fromkeys(intents)
        if item in IntentConstants.SUPPORTED_TYPES
    ]
    if not unique:
        return [IntentConstants.DEFAULT]
    if len(unique) > 1 and IntentConstants.GENERAL_CHAT in unique:
        filtered: list[IntentType] = [
            item for item in unique if item != IntentConstants.GENERAL_CHAT
        ]
        return filtered
    return unique


def is_direct_chat_intent(expression: IntentExpression) -> bool:
    """判断是否为纯闲聊意图，只有闲聊单独出现时才走直连对话"""
    return parse_intent_expression(expression) == [IntentConstants.GENERAL_CHAT]


class StructuredIntent(BaseModel):
    """结构化意图识别结果（优先使用，避免脆弱文本匹配）"""

    types: list[IntentType] = Field(
        default_factory=list,
        description=IntentConstants.STRUCTURED_TYPES_DESCRIPTION,
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description=IntentConstants.STRUCTURED_CONFIDENCE_DESCRIPTION,
    )


class IntentRouter:
    """意图识别路由器，支持权限检查

    优先使用 with_structured_output 结构化输出，不可用时降级为文本匹配
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
    ) -> tuple[IntentExpression, IntentResolution]:
        """异步路由用户问题（优先使用结构化输出，降级为文本匹配）

        意图由模型判定，模型给出多个领域时组合路由，关键词表只在降级链路补信号

        Args:
            question: 用户问题
            runnable_config: LangChain RunnableConfig (用于 LangSmith 追踪)

        Returns:
            (意图表达式, 识别路径)，意图表达式用 | 连接多个领域
        """
        # 复用主链路的 tags/metadata，但意图链自身的 Run 名称固定为 intent.route
        config = dict(runnable_config) if runnable_config else {}
        config["run_name"] = "intent.route"
        try:
            if self._use_structured_output:
                intents, resolution = await self._route_structured(question, config)
            else:
                intents, resolution = await self._route_text_match(question, config)
            return format_intent_expression(intents), resolution
        except Exception as e:
            self.logger.error(Messages.INTENT_RECOGNITION_FAILED(e))
            return IntentConstants.DEFAULT, "default_fallback"

    async def _route_structured(
        self, question: str, config: dict
    ) -> tuple[list[IntentType], IntentResolution]:
        """通过 with_structured_output 链识别意图，模型给出的领域集合即为最终结果"""
        try:
            result: Any = await self.structured_chain.ainvoke(
                {"question": question}, config=config
            )
            if isinstance(result, str):
                # 模型忽略了结构化约束，按文本解析并补齐多领域信号
                primary = self._resolve_text_intent(result)
                return self._merge_text_intents(question, primary), "text_fallback"
            model_types = list(getattr(result, "types", None) or [])
            intents = normalize_intents(model_types)
            self.logger.info(
                Messages.INTENT_STRUCTURED_RESULT(
                    question, format_intent_expression(intents), result.confidence
                )
            )
            return intents, "structured" if model_types else "default_fallback"
        except Exception as e:
            # 结构化输出失败，降级为文本匹配
            self.logger.warning(Messages.INTENT_STRUCTURED_FALLBACK(e))
            return await self._route_text_match(question, config)

    async def _route_text_match(
        self, question: str, config: dict
    ) -> tuple[list[IntentType], IntentResolution]:
        """通过文本匹配识别意图（降级方案），关键词表仅在此链路补齐多领域"""
        result: Any = await self.chain.ainvoke({"question": question}, config=config)
        result_text: str = str(result).strip().lower()

        primary = self._resolve_text_intent(result_text)
        intents = self._merge_text_intents(question, primary)

        self.logger.info(
            Messages.INTENT_TEXT_RESULT(question, format_intent_expression(intents))
        )
        return intents, "text_fallback"

    @staticmethod
    def _resolve_text_intent(result_text: str) -> IntentType:
        """将模型返回的意图文本转换为系统支持的意图类型，按关键词表优先级取首个命中"""
        matched = IntentRouter._resolve_text_intents(result_text)
        return matched[0] if matched else IntentConstants.DEFAULT

    @staticmethod
    def _resolve_text_intents(text: str) -> list[IntentType]:
        """挑出文本中出现的全部意图，顺序与关键词表优先级一致"""
        normalized = str(text).strip().lower()
        return [
            intent
            for intent, patterns in _INTENT_MARKER_PATTERNS
            if any(pattern.search(normalized) for pattern in patterns)
        ]

    @classmethod
    def _merge_text_intents(
        cls, question: str, primary: IntentType
    ) -> list[IntentType]:
        """文本降级链路按问题中的能力信号补充多领域意图

        单个关键词只作为交叉校验信号，至少两个信号同时出现才组合路由；
        闲聊被关键词接管同样要求两个信号，避免“推荐一首歌”这类请求误入工具链路
        """
        detected: list[IntentType] = [
            intent
            for intent in cls._resolve_text_intents(question)
            if intent != IntentConstants.GENERAL_CHAT
        ]
        if len(detected) < 2:
            return [primary]
        if primary == IntentConstants.GENERAL_CHAT:
            return detected
        merged: list[IntentType] = [primary]
        merged.extend(item for item in detected if item != primary)
        return merged

    async def route_with_permission_check_async(
        self,
        question: str,
        user_id: Optional[int] = None,
        db: Optional[Session] = None,
        runnable_config: Optional[dict] = None,
    ) -> tuple[IntentExpression, bool, str, IntentResolution]:
        """异步路由用户问题并检查权限

        Returns:
            (意图表达式, 是否有权限, 权限消息, 识别路径)，意图表达式用 | 连接多个领域
        """
        intent, resolution = await self.route_async(question, runnable_config)
        intents = parse_intent_expression(intent)
        # 回传规范化后的表达式，保证权限校验用的意图集合与返回内容一致
        intent = format_intent_expression(intents)

        if user_id is not None and db is not None:
            self.user_id = user_id
            self.db = db

        # 意图集合来自模型判定，不再由关键词表扩写，未登录时只有模型认出的受限域才拒绝
        if not self.user_id or not self.db:
            if any(item in IntentConstants.RESTRICTED for item in intents):
                return (
                    intent,
                    False,
                    Messages.INTENT_ROUTER_NO_PERMISSION_ERROR,
                    resolution,
                )
            return intent, True, "", resolution

        perm_manager: UserPermissionManager = get_user_permission_manager()

        # 所有意图统一建立工具作用域：admin 全量数据，非 admin 限定本人行级范围
        role = await perm_manager.get_user_role_async(self.user_id, self.db)
        perm_manager.apply_tool_scope(self.user_id, role)

        # 组合意图逐项校验受限领域，任一领域无权限即整体拒绝：
        # agent 共用同一套工具集，无法按意图裁剪工具，因此不做部分放行
        if "database_query" in intents:
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
                self.user_id, self.db, question, role=role
            )
            if not has_permission:
                return intent, False, msg, resolution
            if len(intents) == 1:
                return intent, True, "", resolution

        if "log_analysis" in intents:
            has_permission, msg = await perm_manager.can_access_mongodb_logs_async(
                self.user_id, self.db, question, role=role
            )
            if not has_permission:
                return intent, False, msg, resolution

        return intent, True, "", resolution
