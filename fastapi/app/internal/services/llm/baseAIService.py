import os
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from app.core.base import Constants, Logger
from app.core.config import load_config
from app.internal.agents import (
    IntentRouter,
    get_mongodb_tools,
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
            ("system", Constants.AGENT_PROMPT_TEMPLATE),
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
            Logger.info(f"已加载 SQL 工具: {len(sql_tools)} 个")
        except Exception as e:
            Logger.warning(f"加载 SQL 工具失败: {e}")

    # 获取 RAG 工具
    try:
        rag_tools_instance = get_rag_tools()
        rag_tools: List[Any] = rag_tools_instance.get_langchain_tools()
        all_tools.extend(rag_tools)
        Logger.info(f"已加载 RAG 工具: {len(rag_tools)} 个")
    except Exception as e:
        Logger.warning(f"加载 RAG 工具失败: {e}")

    # 获取 MongoDB 日志工具
    if include_logs:
        try:
            mongodb_tools_instance = get_mongodb_tools()
            mongodb_tools: List[Any] = mongodb_tools_instance.get_langchain_tools()
            all_tools.extend(mongodb_tools)
            Logger.info(f"已加载 MongoDB 日志工具: {len(mongodb_tools)} 个")
        except Exception as e:
            Logger.warning(f"加载 MongoDB 日志工具失败: {e}")

    Logger.info(f"总共加载了 {len(all_tools)} 个工具")
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
        return Constants.CONTENT_SUMMARIZE_PROMPT.format(
            content=content, max_length=max_length
        )

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
        return Constants.REFERENCE_BASED_EVALUATION_PROMPT.format(
            reference_content=reference_content, message=message
        )

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
            Logger.error(f"加载聊天历史失败: {e}")
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

                step_text = f"\n步骤 {i}:\n"
                step_text += f"  工具: {tool_name}\n"
                step_text += f"  输入: {tool_input}\n"
                step_text += f"  结果: {observation}\n"

                thinking_parts.append(step_text)

        # 添加最终结果
        if final_result:
            thinking_parts.append(f"\n\n最终分析结果:\n{final_result}")

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
                + "\n".join([f"用户: {h}\nAI: {a}" for h, a in chat_history[-3:]])
                + "\n\n"
            )
        return context

    def _normalize_user_id(self, user_id: Any) -> Optional[int]:
        """将用户ID统一转换为整数，避免不同调用链传入字符串。"""
        if user_id is None:
            return None

        try:
            user_id_text = str(user_id).strip()
            if not user_id_text:
                return None
            return int(user_id_text)
        except (TypeError, ValueError):
            Logger.warning(f"用户ID格式不合法，已忽略: {user_id}")
            return None

    def _reset_runtime_state(self) -> None:
        """重置运行时状态，方便配置初始化失败后的降级。"""
        self.llm = None
        self.agent = None
        self.agent_executor = None
        self.intent_router = None
        self.all_tools = []

    def _build_initialization_success_message(self) -> str:
        return f"{self.service_name} Agent服务初始化完成"

    def _build_configuration_incomplete_message(self) -> str:
        return f"{self.service_name}配置不完整，客户端未初始化"

    def _build_client_initialization_error_message(self, error: Exception) -> str:
        return f"初始化{self.service_name}客户端失败: {error}"

    def _build_invalid_api_key_error_message(self) -> str:
        return f"API密钥无效。请检查{self.service_name} API密钥配置。"

    def _build_quota_exceeded_error_message(self) -> str:
        return f"{self.service_name} API 配额已用完。请稍后重试。"

    def _build_rate_limit_exceeded_error_message(self) -> str:
        return f"{self.service_name} API调用频率超限。请稍后重试。"

    def _build_call_failed_error_message(self) -> str:
        return f"{self.service_name}调用失败"

    def _resolve_service_error_message(self, error_message: str) -> str:
        """把底层模型错误映射成可读的中文提示。"""
        lower_error = error_message.lower()
        if "invalid" in lower_error and "key" in lower_error:
            return self._build_invalid_api_key_error_message()
        if "quota" in lower_error or "exceeded" in lower_error:
            return self._build_quota_exceeded_error_message()
        if "rate" in lower_error and "limit" in lower_error:
            return self._build_rate_limit_exceeded_error_message()
        if "timeout" in lower_error:
            return Constants.REQUEST_TIMEOUT_ERROR
        return f"{self.service_name}服务异常: {error_message}"

    def _initialize_agent_stack(
        self, user_mapper: Optional[Any], max_iterations: int = 5
    ) -> None:
        """初始化工具、意图路由器和 Agent。"""
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
            Logger.warning(f"工具初始化部分失败: {tool_error}, 降级为基础对话模式")
            self.agent = None
            self.agent_executor = None
            self.intent_router = None

    def _initialize_llm_service(self, user_mapper: Optional[Any] = None) -> None:
        """从配置中初始化 CloseAI 客户端和 Agent 能力。"""
        try:
            service_cfg: Dict[str, Any] = load_config(self.config_section) or {}
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
            Logger.info(f"基础对话: {message}")

            if not getattr(self, "llm", None):
                return Constants.INITIALIZATION_ERROR

            messages = [
                SystemMessage(content=Constants.CHAT_SYSTEM_MESSAGE),
                HumanMessage(content=message),
            ]
            response = await self.llm.ainvoke(messages)

            result: str = response.content
            Logger.info(f"{self.service_name}基础回复长度: {len(result)} 字符")
            return result

        except Exception as error:
            Logger.error(f"{self.service_name}基础对话异常: {str(error)}")
            return f"对话服务异常: {str(error)}"

    async def with_reference_chat(self, message: str, reference_content: str) -> str:
        """基于参考文本进行评价和打分。"""
        try:
            Logger.info(f"基于参考文本的对话（长度: {len(reference_content)}）")

            if not getattr(self, "llm", None):
                return Constants.INITIALIZATION_ERROR

            prompt = self._get_reference_evaluation_prompt(message, reference_content)
            messages = [
                SystemMessage(content=Constants.REFERENCE_CHAT_MESSAGE),
                HumanMessage(content=prompt),
            ]

            response = await self.llm.ainvoke(messages)
            result: str = response.content
            Logger.info(f"{self.service_name}参考文本对话回复长度: {len(result)} 字符")
            return result

        except Exception as error:
            Logger.error(f"{self.service_name}参考文本对话异常: {str(error)}")
            return f"对话服务异常: {str(error)}"

    async def summarize_content(self, content: str, max_length: int = 1000) -> str:
        """总结长文本内容"""
        try:
            Logger.info(
                f"{self.service_name}开始总结内容，原始长度: {len(content)} 字符"
            )

            if not getattr(self, "llm", None):
                return Constants.INITIALIZATION_ERROR

            prompt = self._get_summarize_prompt(content, max_length)
            messages = [
                SystemMessage(content=Constants.SUMMARIZE_CHAT_MESSAGE),
                HumanMessage(content=prompt),
            ]

            response = await self.llm.ainvoke(messages)
            result: str = response.content[:max_length]
            Logger.info(
                f"{self.service_name}内容总结完成，总结长度: {len(result)} 字符"
            )
            return result

        except Exception as error:
            Logger.error(f"{self.service_name}内容总结异常: {str(error)}")
            return f"总结服务异常: {str(error)}"

    async def simple_chat(
        self, message: str, user_id: int | str = 0, db: Optional[Session] = None
    ) -> str:
        """普通聊天接口"""
        try:
            normalized_user_id = self._normalize_user_id(user_id)
            Logger.info(f"用户 {user_id} 发送消息: {message}")

            if not getattr(self, "llm", None):
                return Constants.INITIALIZATION_ERROR

            if not self.agent_executor:
                return await self.basic_chat(message)

            intent = "general_chat"
            if self.intent_router and db and normalized_user_id is not None:
                (
                    intent,
                    has_permission,
                    permission_msg,
                ) = await self.intent_router.route_with_permission_check_async(
                    message, normalized_user_id, db
                )
                Logger.info(f"识别意图: {intent}, 有权限: {has_permission}")

                if not has_permission:
                    Logger.info(f"用户 {user_id} 无权限访问: {intent}")
                    return permission_msg or Constants.NO_PERMISSION_ERROR
            elif self.intent_router:
                intent = await self.intent_router.route_async(message)
                Logger.info(f"识别意图: {intent}")

            chat_history: List[ChatHistoryItem] = []
            if db and normalized_user_id is not None:
                chat_history = await self._load_chat_history(normalized_user_id, db)

            if intent == "general_chat":
                history_messages: list[Any] = []
                for human_msg, ai_msg in chat_history:
                    history_messages.append(HumanMessage(content=human_msg))
                    history_messages.append(AIMessage(content=ai_msg))

                messages = [
                    SystemMessage(content=Constants.GENERIC_CHAT_MESSAGE),
                    *history_messages,
                    HumanMessage(content=message),
                ]
                response = await self.llm.ainvoke(messages)
                result = response.content
            else:
                Logger.info(Constants.AGENT_PROCESSING_MESSAGE)

                if normalized_user_id is not None:
                    try:
                        sql_tools = get_sql_tools()
                        sql_tools.set_user_id(normalized_user_id)
                        Logger.info(f"为SQL工具设置用户ID: {normalized_user_id}")
                    except Exception as error:
                        Logger.warning(f"设置SQL工具用户ID失败: {error}")

                context = self._build_chat_context(chat_history)
                user_info = (
                    f"当前用户ID: {normalized_user_id}\n" if normalized_user_id else ""
                )
                full_input = context + user_info + f"当前问题: {message}"

                agent_response = await self.agent_executor.ainvoke(
                    {"input": full_input}
                )
                result = agent_response.get("output", Constants.MESSAGE_RETRIEVAL_ERROR)

            Logger.info(f"{self.service_name}回复长度: {len(result)} 字符")
            return result

        except Exception as error:
            Logger.error(f"{self.service_name}聊天异常: {str(error)}")
            return self._resolve_service_error_message(str(error))

    async def stream_chat(
        self, message: str, user_id: int | str = 0, db: Optional[Session] = None
    ) -> AsyncGenerator[dict[str, str], None]:
        """流式聊天接口"""
        try:
            normalized_user_id = self._normalize_user_id(user_id)
            Logger.info(f"用户 {user_id} 开始流式聊天: {message}")

            if not getattr(self, "llm", None):
                yield {"type": "error", "content": Constants.INITIALIZATION_ERROR}
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
                    SystemMessage(content=Constants.GENERIC_CHAT_MESSAGE),
                    *history_messages,
                    HumanMessage(content=message),
                ]

                try:
                    async for chunk in self.llm.astream(messages):
                        try:
                            if chunk.content:
                                Logger.debug(
                                    f"收到流式内容块，长度: {len(chunk.content)} 字符"
                                )
                                yield {"type": "content", "content": chunk.content}
                        except Exception as chunk_error:
                            Logger.error(f"处理流式内容块异常: {str(chunk_error)}")
                            continue
                except Exception as stream_error:
                    error_msg = str(stream_error)
                    Logger.error(f"基础流式对话失败: {error_msg}")
                    yield {
                        "type": "content",
                        "content": self._resolve_service_error_message(error_msg),
                    }
                return

            intent = "general_chat"
            if self.intent_router and db and normalized_user_id is not None:
                (
                    intent,
                    has_permission,
                    permission_msg,
                ) = await self.intent_router.route_with_permission_check_async(
                    message, normalized_user_id, db
                )
                Logger.info(f"识别意图: {intent}, 有权限: {has_permission}")

                if not has_permission:
                    Logger.info(f"用户 {user_id} 无权限访问: {intent}")
                    permission_message = permission_msg or Constants.NO_PERMISSION_ERROR
                    thinking = f"检测到用户请求需要 {intent} 权限，但当前用户权限不足。"
                    yield {"type": "thinking", "content": thinking}

                    for char in permission_message:
                        yield {"type": "content", "content": char}
                    return

            elif self.intent_router:
                intent = await self.intent_router.route_async(message)
                Logger.info(f"识别意图: {intent}")

            chat_history = []
            if db and normalized_user_id is not None:
                chat_history = await self._load_chat_history(normalized_user_id, db)

            if intent == "general_chat":
                history_messages: list[Any] = []
                for human_msg, ai_msg in chat_history:
                    history_messages.append(HumanMessage(content=human_msg))
                    history_messages.append(AIMessage(content=ai_msg))

                messages = [
                    SystemMessage(content=Constants.GENERIC_CHAT_MESSAGE),
                    *history_messages,
                    HumanMessage(content=message),
                ]

                try:
                    async for chunk in self.llm.astream(messages):
                        try:
                            if chunk.content:
                                yield {"type": "content", "content": chunk.content}
                        except Exception as chunk_error:
                            Logger.error(f"处理流式内容块异常: {str(chunk_error)}")
                            continue
                except Exception as stream_error:
                    error_msg = str(stream_error)
                    Logger.error(f"流式聊天失败: {error_msg}")
                    yield {
                        "type": "content",
                        "content": self._resolve_service_error_message(error_msg),
                    }
            else:
                Logger.info(Constants.AGENT_PROCESSING_MESSAGE)

                if normalized_user_id is not None:
                    try:
                        sql_tools = get_sql_tools()
                        sql_tools.set_user_id(normalized_user_id)
                        Logger.info(f"为SQL工具设置用户ID: {normalized_user_id}")
                    except Exception as error:
                        Logger.warning(f"设置SQL工具用户ID失败: {error}")

                context = self._build_chat_context(chat_history)
                user_info = (
                    f"当前用户ID: {normalized_user_id}\n" if normalized_user_id else ""
                )
                full_input = context + user_info + f"当前问题: {message}"

                Logger.info(Constants.AGENT_START_PROCESSING_MESSAGE)
                try:
                    agent_response = await self.agent_executor.ainvoke(
                        {
                            "input": full_input,
                            "system_message": Constants.STREAMING_CHAT_THINKING_SYSTEM_MESSAGE,
                        }
                    )
                    agent_result = agent_response.get(
                        "output", Constants.MESSAGE_RETRIEVAL_ERROR
                    )
                except Exception as agent_error:
                    error_msg = str(agent_error)
                    Logger.error(f"Agent执行失败: {error_msg}")
                    yield {
                        "type": "content",
                        "content": self._resolve_service_error_message(error_msg),
                    }
                    return

                intermediate_steps = agent_response.get("intermediate_steps", [])
                thinking_text = self._build_complete_thinking_text(
                    intermediate_steps, agent_result
                )

                Logger.info(f"思考过程长度: {len(thinking_text)} 字符")
                if len(thinking_text) > 5000:
                    Logger.debug(f"思考过程内容（前2000字）: {thinking_text[:2000]}")
                    Logger.debug(
                        f"思考过程内容（中间2000字）: {thinking_text[len(thinking_text) // 2 - 1000 : len(thinking_text) // 2 + 1000]}"
                    )
                    Logger.debug(f"思考过程内容（末尾2000字）: {thinking_text[-2000:]}")
                else:
                    Logger.debug(f"完整思考过程: {thinking_text}")

                yield {"type": "thinking", "content": thinking_text}

                Logger.info(Constants.AGENT_START_STREAMING_MESSAGE)

                history_messages = []
                for human_msg, ai_msg in chat_history:
                    history_messages.append(HumanMessage(content=human_msg))
                    history_messages.append(AIMessage(content=ai_msg))

                stream_messages = [
                    SystemMessage(content=Constants.GENERIC_CHAT_MESSAGE),
                    *history_messages,
                    HumanMessage(
                        content=(
                            f"用户问题: {message}\n\n我已经获取到以下信息:\n{agent_result}\n\n"
                            "请基于这些信息,用清晰、友好的方式回答用户的问题。"
                        )
                    ),
                ]

                try:
                    async for chunk in self.llm.astream(stream_messages):
                        try:
                            if chunk.content:
                                yield {"type": "content", "content": chunk.content}
                        except Exception as chunk_error:
                            Logger.error(f"处理流式内容块异常: {str(chunk_error)}")
                            continue
                except Exception as final_stream_error:
                    error_msg = str(final_stream_error)
                    Logger.error(f"最终流式输出失败: {error_msg}")
                    yield {
                        "type": "content",
                        "content": self._resolve_service_error_message(error_msg),
                    }

        except Exception as error:
            Logger.error(f"流式聊天异常: {str(error)}")
            yield {
                "type": "error",
                "content": self._resolve_service_error_message(str(error)),
            }
