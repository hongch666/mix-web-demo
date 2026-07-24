import os
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from app.core.base import Logger
from app.core.config import load_config
from app.core.constants import Messages, Prompts
from app.internal.agents import (
    IntentRouter,
    get_mongodb_tools,
    get_neo4j_tools,
    get_rag_tools,
    get_sql_tools,
)
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

ChatHistoryItem = Tuple[str, str]
IntermediateStep = Tuple[Any, Any]


def get_agent_prompt() -> ChatPromptTemplate:
    """获取Agent的Prompt模板"""
    return ChatPromptTemplate.from_messages(
        [
            ("system", Prompts.AGENT_PROMPT()),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )


def initialize_ai_tools(
    include_sql: bool = True, include_logs: bool = True
) -> Tuple[Optional[Any], Optional[Any], Optional[Any], List[Any]]:
    """初始化AI工具，支持基于权限的工具选择

    Args:
        user_id: 用户ID（用于权限检查）
        db: 数据库会话（用于权限检查）
        include_sql: 是否包含 SQL 工具
        include_logs: 是否包含 MongoDB 日志工具

    Returns:
        tuple: (sql_tools_instance, rag_tools_instance, mongodb_log_tools_instance, all_tools)
    """
    sql_tools_instance: Optional[Any] = None
    rag_tools_instance: Optional[Any] = None
    mongodb_tools_instance: Optional[Any] = None
    all_tools: List[Any] = []

    # 获取 SQL 工具
    if include_sql:
        try:
            sql_tools_instance = get_sql_tools()
            sql_tools: List[Any] = sql_tools_instance.get_langchain_tools()
            all_tools.extend(sql_tools)
            Logger.info(Messages.LLM_TOOL_LOADED("SQL", len(sql_tools)))
        except Exception as e:
            Logger.warning(Messages.LLM_TOOL_LOAD_FAILED("SQL", e))

    # 获取 RAG 工具
    try:
        rag_tools_instance = get_rag_tools()
        rag_tools: List[Any] = rag_tools_instance.get_langchain_tools()
        all_tools.extend(rag_tools)
        Logger.info(Messages.LLM_TOOL_LOADED("RAG", len(rag_tools)))
    except Exception as e:
        Logger.warning(Messages.LLM_TOOL_LOAD_FAILED("RAG", e))

    # 获取 Neo4j 知识图谱工具
    try:
        neo4j_tools_instance = get_neo4j_tools()
        neo4j_tools: List[Any] = neo4j_tools_instance.get_langchain_tools()
        all_tools.extend(neo4j_tools)
        Logger.info(Messages.LLM_TOOL_LOADED("Neo4j 知识图谱", len(neo4j_tools)))
    except Exception as e:
        Logger.warning(Messages.LLM_TOOL_LOAD_FAILED("Neo4j 知识图谱", e))

    # 获取 MongoDB 日志工具
    if include_logs:
        try:
            mongodb_tools_instance = get_mongodb_tools()
            mongodb_tools: List[Any] = mongodb_tools_instance.get_langchain_tools()
            all_tools.extend(mongodb_tools)
            Logger.info(Messages.LLM_TOOL_LOADED("MongoDB 日志", len(mongodb_tools)))
        except Exception as e:
            Logger.warning(Messages.LLM_TOOL_LOAD_FAILED("MongoDB 日志", e))

    Logger.info(Messages.LLM_TOOLS_LOADED_TOTAL(len(all_tools)))
    return sql_tools_instance, rag_tools_instance, mongodb_tools_instance, all_tools


class BaseAiService:
    """AI服务基类"""

    def __init__(
        self,
        ai_history_mapper: Any,
        service_name: str = "AI",
        config_section: str = "closeai",
        model_config_key: str = "model_name",
        user_mapper: Optional[Any] = None,
        temperature: float = 0.7,
    ) -> None:
        self._normalize_proxy_env()
        self.ai_history_mapper: Any = ai_history_mapper
        self.service_name: str = service_name
        self.config_section: str = config_section
        self.model_config_key: str = model_config_key
        self.temperature: float = temperature
        self.llm: Optional[Any] = None
        self.agent: Optional[Any] = None
        self.agent_executor: Optional[Any] = None
        self.intent_router: Optional[Any] = None
        self.all_tools: List[Any] = []
        self.model_name: str = ""
        self._api_key: str = ""
        self._base_url: str = ""
        self._timeout: int = 30

        self._initialize_llm_service(user_mapper=user_mapper)

    @staticmethod
    def _normalize_proxy_env() -> None:
        proxy_keys = [
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ALL_PROXY",
            "http_proxy",
            "https_proxy",
            "all_proxy",
        ]
        for key in proxy_keys:
            value = os.getenv(key)
            if value and value.startswith("socks://"):
                os.environ[key] = value.replace("socks://", "socks5://", 1)

    def _get_summarize_prompt(self, content: str, max_length: int = 1000) -> str:
        """获取内容总结提示词

        Args:
            content: 需要总结的内容
            max_length: 最大总结长度

        Returns:
            str: 格式化后的提示词
        """
        return Prompts.CONTENT_SUMMARIZE(content, max_length)

    def _get_reference_evaluation_prompt(
        self, message: str, reference_content: str
    ) -> str:
        """获取基于参考文本的评价提示词

        Args:
            message: 待评价内容
            reference_content: 权威参考文本

        Returns:
            str: 格式化后的提示词
        """
        return Prompts.REFERENCE_BASED_EVALUATION(message, reference_content)

    async def _load_chat_history(
        self, user_id: int, db: Session
    ) -> List[ChatHistoryItem]:
        """从数据库加载聊天历史"""
        try:
            histories = await self.ai_history_mapper.get_all_ai_history_by_userid_async(
                db, user_id, 5
            )
            chat_history: List[ChatHistoryItem] = []
            for h in histories:
                chat_history.append((h.ask, h.reply))
            return chat_history
        except Exception as e:
            Logger.error(Messages.LLM_CHAT_HISTORY_LOAD_FAILED(e))
            return []

    def _build_complete_thinking_text(
        self, intermediate_steps: List[IntermediateStep], final_result: str = ""
    ) -> str:
        """构建完整的思考过程文本（包含最终结果）

        Args:
            intermediate_steps: Agent的中间步骤列表
            final_result: Agent的最终结果

        Returns:
            str: 完整的思考过程文本
        """
        thinking_parts = []

        # 构建中间步骤
        if intermediate_steps:
            thinking_parts.append("Agent 执行过程:\n")
            for i, (action, observation) in enumerate(intermediate_steps, 1):
                tool_name = action.tool if hasattr(action, "tool") else str(action)
                tool_input = action.tool_input if hasattr(action, "tool_input") else ""

                step_text = Messages.AGENT_EXECUTION_STEP(i, tool_name, str(tool_input), str(observation))

                thinking_parts.append(step_text)

        # 添加最终结果
        if final_result:
            thinking_parts.append(Messages.AGENT_FINAL_RESULT(final_result))

        # 拼接所有部分
        complete_text = "".join(thinking_parts)
        return complete_text

    def _build_chat_context(self, chat_history: List[ChatHistoryItem]) -> str:
        """构建聊天历史上下文

        Args:
            chat_history: 聊天历史列表

        Returns:
            str: 格式化的历史对话上下文
        """
        context = ""
        if chat_history:
            context = (
                "\n\n历史对话:\n"
                + "\n".join([Messages.CHAT_HISTORY_LINE(h, a) for h, a in chat_history[-3:]])
                + "\n\n"
            )
        return context

    def _normalize_user_id(self, user_id: Any) -> Optional[int]:
        """将用户ID统一转换为整数，避免不同调用链传入字符串"""
        if user_id is None:
            return None

        try:
            user_id_text = str(user_id).strip()
            if not user_id_text:
                return None
            return int(user_id_text)
        except (TypeError, ValueError):
            Logger.warning(Messages.LLM_INVALID_USER_ID(user_id))
            return None

    def _reset_runtime_state(self) -> None:
        """重置运行时状态，方便配置初始化失败后的降级"""
        self.llm = None
        self.agent = None
        self.agent_executor = None
        self.intent_router = None
        self.all_tools = []

    def _build_initialization_success_message(self) -> str:
        return Messages.LLM_INITIALIZATION_SUCCESS(self.service_name)

    def _build_configuration_incomplete_message(self) -> str:
        return Messages.LLM_CONFIGURATION_INCOMPLETE(self.service_name)

    def _build_client_initialization_error_message(self, error: Exception) -> str:
        return Messages.LLM_CLIENT_INITIALIZATION_FAILED(self.service_name, error)

    def _build_invalid_api_key_error_message(self) -> str:
        return Messages.LLM_INVALID_API_KEY(self.service_name)

    def _build_quota_exceeded_error_message(self) -> str:
        return Messages.LLM_QUOTA_EXCEEDED(self.service_name)

    def _build_rate_limit_exceeded_error_message(self) -> str:
        return Messages.LLM_RATE_LIMIT_EXCEEDED(self.service_name)

    def _build_call_failed_error_message(self) -> str:
        return Messages.LLM_CALL_FAILED(self.service_name)

    def _resolve_service_error_message(self, error_message: str) -> str:
        """把底层模型错误映射成可读的中文提示"""
        lower_error = error_message.lower()
        if "invalid" in lower_error and "key" in lower_error:
            return self._build_invalid_api_key_error_message()
        if "quota" in lower_error or "exceeded" in lower_error:
            return self._build_quota_exceeded_error_message()
        if "rate" in lower_error and "limit" in lower_error:
            return self._build_rate_limit_exceeded_error_message()
        if "timeout" in lower_error:
            return Messages.REQUEST_TIMEOUT_ERROR
        return Messages.LLM_SERVICE_ERROR(self.service_name, error_message)

    def _initialize_agent_stack(
        self, user_mapper: Optional[Any], max_iterations: int = 5
    ) -> None:
        """初始化工具、意图路由器和 Agent"""
        try:
            _, _, _, self.all_tools = initialize_ai_tools()
            self.intent_router = IntentRouter(self.llm, user_mapper=user_mapper)

            agent_prompt = get_agent_prompt()
            self.agent = create_tool_calling_agent(
                llm=self.llm,
                tools=self.all_tools,
                prompt=agent_prompt,
            )
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.all_tools,
                verbose=True,
                handle_parsing_errors=False,
                max_iterations=max_iterations,
                return_intermediate_steps=True,
            )
        except Exception as tool_error:
            Logger.warning(Messages.LLM_AGENT_INITIALIZATION_PARTIAL_FAILED(tool_error))
            self.agent = None
            self.agent_executor = None
            self.intent_router = None

    def _initialize_llm_service(self, user_mapper: Optional[Any] = None) -> None:
        """从配置中初始化 CloseAI 客户端和 Agent 能力"""
        try:
            service_cfg: Dict[str, Any] = (load_config("agent") or {}).get(
                self.config_section
            ) or {}
            self._api_key = str(service_cfg.get("api_key") or "").strip()
            self._base_url = str(service_cfg.get("base_url") or "").strip()
            timeout_value = service_cfg.get("timeout", self._timeout)
            self._timeout = int(timeout_value) if timeout_value else self._timeout
            self.model_name = str(
                service_cfg.get(self.model_config_key)
                or service_cfg.get("model_name")
                or ""
            ).strip()
            agent_max_iterations = int(service_cfg.get("agent_max_iterations", 8))

            if self._api_key and self._base_url and self.model_name:
                self.llm = ChatOpenAI(
                    model=self.model_name,
                    api_key=self._api_key,
                    base_url=self._base_url,
                    temperature=self.temperature,
                    timeout=self._timeout,
                )
                self._initialize_agent_stack(
                    user_mapper=user_mapper, max_iterations=agent_max_iterations
                )
                Logger.info(self._build_initialization_success_message())
            else:
                self._reset_runtime_state()
                Logger.warning(self._build_configuration_incomplete_message())
        except Exception as error:
            self._reset_runtime_state()
            Logger.error(self._build_client_initialization_error_message(error))

    async def basic_chat(self, message: str) -> str:
        """最基础的对话接口 - 不使用知识库和向量数据库"""
        try:
            Logger.info(Messages.BASIC_CHAT_START(message))

            if not getattr(self, "llm", None):
                return Messages.INITIALIZATION_ERROR

            messages = [
                SystemMessage(content=Messages.CHAT_SYSTEM_MESSAGE),
                HumanMessage(content=message),
            ]
            response = await self.llm.ainvoke(messages)

            result: str = response.content
            Logger.info(Messages.BASIC_CHAT_REPLY_LENGTH(self.service_name, len(result)))
            return result

        except Exception as error:
            Logger.error(Messages.BASIC_CHAT_EXCEPTION(self.service_name, str(error)))
            return Messages.CHAT_SERVICE_ERROR(error)

    async def with_reference_chat(self, message: str, reference_content: str) -> str:
        """基于参考文本进行评价和打分"""
        try:
            Logger.info(Messages.REFERENCE_CHAT_START(len(reference_content)))

            if not getattr(self, "llm", None):
                return Messages.INITIALIZATION_ERROR

            prompt = self._get_reference_evaluation_prompt(message, reference_content)
            messages = [
                SystemMessage(content=Messages.REFERENCE_CHAT_MESSAGE),
                HumanMessage(content=prompt),
            ]

            response = await self.llm.ainvoke(messages)
            result: str = response.content
            Logger.info(Messages.REFERENCE_CHAT_REPLY_LENGTH(self.service_name, len(result)))
            return result

        except Exception as error:
            Logger.error(Messages.REFERENCE_CHAT_EXCEPTION(self.service_name, str(error)))
            return Messages.CHAT_SERVICE_ERROR(error)

    async def summarize_content(self, content: str, max_length: int = 1000) -> str:
        """总结长文本内容"""
        try:
            Logger.info(
                Messages.SUMMARIZE_START(self.service_name, len(content))
            )

            if not getattr(self, "llm", None):
                return Messages.INITIALIZATION_ERROR

            prompt = self._get_summarize_prompt(content, max_length)
            messages = [
                SystemMessage(content=Messages.SUMMARIZE_CHAT_MESSAGE),
                HumanMessage(content=prompt),
            ]

            response = await self.llm.ainvoke(messages)
            result: str = response.content[:max_length]
            Logger.info(
                Messages.SUMMARIZE_COMPLETED(self.service_name, len(result))
            )
            return result

        except Exception as error:
            Logger.error(Messages.SUMMARIZE_EXCEPTION(self.service_name, str(error)))
            return Messages.SUMMARIZE_SERVICE_ERROR(error)

    async def simple_chat(
        self,
        message: str,
        user_id: int | str = 0,
        db: Optional[Session] = None,
        runnable_config: Optional[dict] = None,
    ) -> str:
        """普通聊天接口

        Args:
            message: 用户消息
            user_id: 用户ID
            db: 数据库会话
            runnable_config: LangChain RunnableConfig (用于 LangSmith 追踪传播)
        """
        try:
            normalized_user_id = self._normalize_user_id(user_id)
            Logger.info(Messages.USER_SEND_MESSAGE(user_id, message))

            if not getattr(self, "llm", None):
                return Messages.INITIALIZATION_ERROR

            if not self.agent_executor:
                return await self.basic_chat(message)

            intent = "general_chat"
            intent_resolution = "default_fallback"
            if self.intent_router and db and normalized_user_id is not None:
                (
                    intent,
                    has_permission,
                    permission_msg,
                    intent_resolution,
                ) = await self.intent_router.route_with_permission_check_async(
                    message, normalized_user_id, db
                )
                Logger.info(Messages.INTENT_WITH_PERMISSION(intent, has_permission))

                if not has_permission:
                    Logger.info(Messages.USER_NO_PERMISSION_FOR_INTENT(user_id, intent))
                    return permission_msg or Messages.NO_PERMISSION_ERROR
            elif self.intent_router:
                intent, intent_resolution = await self.intent_router.route_async(message)
                Logger.info(Messages.INTENT_RECOGNIZED(intent))

            # 将意图信息补充到 runnable_config 中
            config = dict(runnable_config) if runnable_config else {}
            config.setdefault("metadata", {})
            config["metadata"].update({
                "intent": intent,
                "intent_resolution": intent_resolution,
            })

            chat_history: List[ChatHistoryItem] = []
            if db and normalized_user_id is not None:
                chat_history = await self._load_chat_history(normalized_user_id, db)

            if intent == "general_chat":
                config.setdefault("run_name", "chat.direct")
                history_messages: list[Any] = []
                for human_msg, ai_msg in chat_history:
                    history_messages.append(HumanMessage(content=human_msg))
                    history_messages.append(AIMessage(content=ai_msg))

                messages = [
                    SystemMessage(content=Messages.GENERIC_CHAT_MESSAGE),
                    *history_messages,
                    HumanMessage(content=message),
                ]
                response = await self.llm.ainvoke(messages, config=config)
                result = response.content
            else:
                Logger.info(Messages.AGENT_PROCESSING_MESSAGE)
                config.setdefault("run_name", "agent.execute")

                if normalized_user_id is not None:
                    try:
                        sql_tools = get_sql_tools()
                        sql_tools.set_user_id(normalized_user_id)
                        Logger.info(Messages.SQL_TOOL_SET_USER_ID(normalized_user_id))
                    except Exception as error:
                        Logger.warning(Messages.SQL_TOOL_SET_USER_ID_FAILED(error))

                context = self._build_chat_context(chat_history)
                user_info = (
                    Messages.CURRENT_USER_ID_INFO(normalized_user_id) if normalized_user_id else ""
                )
                full_input = context + user_info + Messages.CURRENT_QUESTION(message)

                agent_response = await self.agent_executor.ainvoke(
                    {"input": full_input}, config=config
                )
                result = agent_response.get("output", Messages.MESSAGE_RETRIEVAL_ERROR)

            Logger.info(Messages.CHAT_REPLY_LENGTH(self.service_name, len(result)))
            return result

        except Exception as error:
            Logger.error(Messages.CHAT_EXCEPTION(self.service_name, str(error)))
            return self._resolve_service_error_message(str(error))

    async def stream_chat(
        self,
        message: str,
        user_id: int | str = 0,
        db: Optional[Session] = None,
        runnable_config: Optional[dict] = None,
    ) -> AsyncGenerator[dict[str, str], None]:
        """流式聊天接口

        Args:
            message: 用户消息
            user_id: 用户ID
            db: 数据库会话
            runnable_config: LangChain RunnableConfig (用于 LangSmith 追踪传播)
        """
        try:
            normalized_user_id = self._normalize_user_id(user_id)
            Logger.info(Messages.USER_START_STREAMING_CHAT(user_id, message))

            if not getattr(self, "llm", None):
                yield {"type": "error", "content": Messages.INITIALIZATION_ERROR}
                return

            if not self.agent_executor:
                chat_history: List[ChatHistoryItem] = []
                if db and normalized_user_id is not None:
                    chat_history = await self._load_chat_history(normalized_user_id, db)

                history_messages: list[Any] = []
                for human_msg, ai_msg in chat_history:
                    history_messages.append(HumanMessage(content=human_msg))
                    history_messages.append(AIMessage(content=ai_msg))

                messages = [
                    SystemMessage(content=Messages.GENERIC_CHAT_MESSAGE),
                    *history_messages,
                    HumanMessage(content=message),
                ]

                config = dict(runnable_config) if runnable_config else {}
                config.setdefault("run_name", "chat.direct")

                try:
                    async for chunk in self.llm.astream(messages, config=config):
                        try:
                            if chunk.content:
                                Logger.debug(
                                    Messages.STREAM_CHUNK_RECEIVED_LENGTH(len(chunk.content))
                                )
                                yield {"type": "content", "content": chunk.content}
                        except Exception as chunk_error:
                            Logger.error(Messages.STREAM_CHUNK_EXCEPTION(str(chunk_error)))
                            continue
                except Exception as stream_error:
                    error_msg = str(stream_error)
                    Logger.error(Messages.STREAM_BASIC_CHAT_FAILED(error_msg))
                    yield {
                        "type": "content",
                        "content": self._resolve_service_error_message(error_msg),
                    }
                return

            intent = "general_chat"
            intent_resolution = "default_fallback"
            if self.intent_router and db and normalized_user_id is not None:
                (
                    intent,
                    has_permission,
                    permission_msg,
                    intent_resolution,
                ) = await self.intent_router.route_with_permission_check_async(
                    message, normalized_user_id, db
                )
                Logger.info(Messages.INTENT_WITH_PERMISSION(intent, has_permission))

                if not has_permission:
                    Logger.info(Messages.USER_NO_PERMISSION_FOR_INTENT(user_id, intent))
                    permission_message = permission_msg or Messages.NO_PERMISSION_ERROR
                    thinking = Messages.PERMISSION_DENIED_STREAM_THINKING(intent)
                    yield {"type": "thinking", "content": thinking}

                    for char in permission_message:
                        yield {"type": "content", "content": char}
                    return

            elif self.intent_router:
                intent, intent_resolution = await self.intent_router.route_async(message)
                Logger.info(Messages.INTENT_RECOGNIZED(intent))

            # 将意图信息补充到 runnable_config 中
            config = dict(runnable_config) if runnable_config else {}
            config.setdefault("metadata", {})
            config["metadata"].update({
                "intent": intent,
                "intent_resolution": intent_resolution,
            })

            chat_history = []
            if db and normalized_user_id is not None:
                chat_history = await self._load_chat_history(normalized_user_id, db)

            if intent == "general_chat":
                config.setdefault("run_name", "chat.direct")
                history_messages: list[Any] = []
                for human_msg, ai_msg in chat_history:
                    history_messages.append(HumanMessage(content=human_msg))
                    history_messages.append(AIMessage(content=ai_msg))

                messages = [
                    SystemMessage(content=Messages.GENERIC_CHAT_MESSAGE),
                    *history_messages,
                    HumanMessage(content=message),
                ]

                try:
                    async for chunk in self.llm.astream(messages, config=config):
                        try:
                            if chunk.content:
                                yield {"type": "content", "content": chunk.content}
                        except Exception as chunk_error:
                            Logger.error(Messages.STREAM_CHUNK_EXCEPTION(str(chunk_error)))
                            continue
                except Exception as stream_error:
                    error_msg = str(stream_error)
                    Logger.error(Messages.STREAM_CHAT_FAILED(error_msg))
                    yield {
                        "type": "content",
                        "content": self._resolve_service_error_message(error_msg),
                    }
            else:
                Logger.info(Messages.AGENT_PROCESSING_MESSAGE)
                config.setdefault("run_name", "agent.execute")

                if normalized_user_id is not None:
                    try:
                        sql_tools = get_sql_tools()
                        sql_tools.set_user_id(normalized_user_id)
                        Logger.info(Messages.SQL_TOOL_SET_USER_ID(normalized_user_id))
                    except Exception as error:
                        Logger.warning(Messages.SQL_TOOL_SET_USER_ID_FAILED(error))

                context = self._build_chat_context(chat_history)
                user_info = (
                    Messages.CURRENT_USER_ID_INFO(normalized_user_id) if normalized_user_id else ""
                )
                full_input = context + user_info + Messages.CURRENT_QUESTION(message)

                Logger.info(Messages.AGENT_START_PROCESSING_MESSAGE)
                try:
                    agent_response = await self.agent_executor.ainvoke(
                        {
                            "input": full_input,
                            "system_message": Messages.STREAMING_CHAT_THINKING_SYSTEM_MESSAGE,
                        },
                        config=config,
                    )
                    agent_result = agent_response.get(
                        "output", Messages.MESSAGE_RETRIEVAL_ERROR
                    )
                except Exception as agent_error:
                    error_msg = str(agent_error)
                    Logger.error(Messages.AGENT_EXECUTION_FAILED(error_msg))
                    yield {
                        "type": "content",
                        "content": self._resolve_service_error_message(error_msg),
                    }
                    return

                intermediate_steps = agent_response.get("intermediate_steps", [])
                thinking_text = self._build_complete_thinking_text(
                    intermediate_steps, agent_result
                )

                Logger.info(Messages.THINKING_PROCESS_LENGTH(len(thinking_text)))
                if len(thinking_text) > 5000:
                    Logger.debug(Messages.THINKING_PROCESS_PREVIEW_TEXT(thinking_text[:2000]))
                    Logger.debug(
                        Messages.THINKING_PROCESS_MIDDLE_TEXT(thinking_text[len(thinking_text) // 2 - 1000 : len(thinking_text) // 2 + 1000])
                    )
                    Logger.debug(Messages.THINKING_PROCESS_END_TEXT(thinking_text[-2000:]))
                else:
                    Logger.debug(Messages.COMPLETE_THINKING_PROCESS_TEXT(thinking_text))

                yield {"type": "thinking", "content": thinking_text}

                Logger.info(Messages.AGENT_START_STREAMING_MESSAGE)

                history_messages = []
                for human_msg, ai_msg in chat_history:
                    history_messages.append(HumanMessage(content=human_msg))
                    history_messages.append(AIMessage(content=ai_msg))

                stream_messages = [
                    SystemMessage(content=Messages.GENERIC_CHAT_MESSAGE),
                    *history_messages,
                    HumanMessage(
                        content=(
                            Messages.STREAM_FINAL_PROMPT(message, agent_result)
                        )
                    ),
                ]

                try:
                    async for chunk in self.llm.astream(stream_messages, config=config):
                        try:
                            if chunk.content:
                                yield {"type": "content", "content": chunk.content}
                        except Exception as chunk_error:
                            Logger.error(Messages.STREAM_CHUNK_EXCEPTION(str(chunk_error)))
                            continue
                except Exception as final_stream_error:
                    error_msg = str(final_stream_error)
                    Logger.error(Messages.FINAL_STREAM_OUTPUT_FAILED(error_msg))
                    yield {
                        "type": "content",
                        "content": self._resolve_service_error_message(error_msg),
                    }

        except Exception as error:
            Logger.error(Messages.STREAM_CHAT_EXCEPTION(str(error)))
            yield {
                "type": "error",
                "content": self._resolve_service_error_message(str(error)),
            }
