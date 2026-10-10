import os
from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.agents import AgentAction
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import is_memory_user, normalize_user_id
from app.core.base import Logger
from app.core.config import load_config
from app.core.constants import Messages, Prompts
from app.internal.agents import (
    AgentToolFactories,
    IntentRouter,
    default_agent_tool_factories,
    is_direct_chat_intent,
)
from app.internal.crud import AiUserSummaryMapper, get_ai_user_summary_mapper
from app.internal.models import AiUserSummary

from .contextBudget import (
    ChatHistoryItem,
    ContextBudgetConfig,
    ContextPlan,
    estimate_tokens,
    plan_chat_context,
    plan_compact_batch,
)

IntermediateStep = tuple[Any, Any]


def get_agent_prompt() -> ChatPromptTemplate:
    """获取Agent的Prompt模板"""
    return ChatPromptTemplate.from_messages(
        [
            ("system", Prompts.AGENT_PROMPT()),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )


def _load_sql_tools(
    sql_tool_factories: list[tuple[str, Any]],
) -> tuple[Optional[Any], list[Any]]:
    """加载 SQL 工具（在独立线程中执行）"""
    sql_tools_instance: Optional[Any] = None
    tools: list[Any] = []
    for service_name, factory in sql_tool_factories:
        try:
            tool_instance: Any = factory()
            sql_tools: list[Any] = tool_instance.get_langchain_tools()
            tools.extend(sql_tools)
            if sql_tools_instance is None:
                sql_tools_instance = tool_instance
            Logger.info(Messages.LLM_TOOL_LOADED(f"{service_name} SQL", len(sql_tools)))
        except Exception as e:
            Logger.warning(Messages.LLM_TOOL_LOAD_FAILED(f"{service_name} SQL", e))
    return sql_tools_instance, tools


def _load_tool_group(group_name: str, factory: Any) -> tuple[Optional[Any], list[Any]]:
    """加载单个工具组（RAG / Neo4j / MongoDB）"""
    try:
        instance: Any = factory()
        tools: list[Any] = instance.get_langchain_tools()
        Logger.info(Messages.LLM_TOOL_LOADED(group_name, len(tools)))
        return instance, tools
    except Exception as e:
        Logger.warning(Messages.LLM_TOOL_LOAD_FAILED(group_name, e))
        return None, []


def initialize_ai_tools(
    include_sql: bool = True,
    include_logs: bool = True,
    tool_factories: Optional[AgentToolFactories] = None,
) -> tuple[Optional[Any], Optional[Any], Optional[Any], list[Any]]:
    """初始化AI工具，支持基于权限的工具选择

    各组独立工具（SQL/RAG/Neo4j/MongoDB）通过线程池并行加载，
    单个工具组加载失败不影响其他组

    Args:
        include_sql: 是否包含 SQL 工具
        include_logs: 是否包含 MongoDB 日志工具
        tool_factories: 工具组装配工厂集合，由依赖图注入；
            缺省时使用进程内默认装配（各工具工厂自行解析客户端单例）

    Returns:
        tuple: (sql_tools_instance, rag_tools_instance, mongodb_log_tools_instance, all_tools)
    """
    sql_tools_instance: Optional[Any] = None
    rag_tools_instance: Optional[Any] = None
    mongodb_tools_instance: Optional[Any] = None
    all_tools: list[Any] = []

    factories: AgentToolFactories = tool_factories or default_agent_tool_factories()

    # 并行加载所有独立工具组
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures: dict[str, Any] = {}

        if include_sql:
            futures["sql"] = executor.submit(_load_sql_tools, list(factories.sql_tools))
        futures["rag"] = executor.submit(_load_tool_group, *factories.rag)
        futures["neo4j"] = executor.submit(_load_tool_group, *factories.neo4j)
        if include_logs:
            futures["mongodb"] = executor.submit(_load_tool_group, *factories.mongodb)
        futures["warehouse"] = executor.submit(_load_tool_group, *factories.warehouse)

        # 按完成顺序收集结果
        for _future in as_completed(futures.values()):
            pass  # 结果通过闭包变量收集，异常已在子函数内部处理

        # 按固定顺序合并结果，确保 tool 列表顺序一致
        if "sql" in futures:
            sql_tools_instance, sql_tools = futures["sql"].result()
            all_tools.extend(sql_tools)
        if "rag" in futures:
            rag_tools_instance, rag_tools = futures["rag"].result()
            all_tools.extend(rag_tools)
        if "neo4j" in futures:
            _, neo4j_tools = futures["neo4j"].result()
            all_tools.extend(neo4j_tools)
        if "mongodb" in futures:
            mongodb_tools_instance, mongo_tools = futures["mongodb"].result()
            all_tools.extend(mongo_tools)
        if "warehouse" in futures:
            _, warehouse_tools = futures["warehouse"].result()
            all_tools.extend(warehouse_tools)

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
        temperature: float = 0.7,
        use_structured_output: bool = True,
        tool_factories: Optional[AgentToolFactories] = None,
        ai_user_summary_mapper: Optional[AiUserSummaryMapper] = None,
    ) -> None:
        self._normalize_proxy_env()
        self.ai_history_mapper: Any = ai_history_mapper
        # 用户级记忆摘要 Mapper，缺省时回退进程内单例（与 spring_client 处理方式一致）
        self.ai_summary_mapper: AiUserSummaryMapper = (
            ai_user_summary_mapper or get_ai_user_summary_mapper()
        )
        self.service_name: str = service_name
        self.config_section: str = config_section
        self.model_config_key: str = model_config_key
        self.temperature: float = temperature
        self.use_structured_output: bool = use_structured_output
        # 工具组装配工厂由依赖图注入，缺省时回退进程内默认装配
        self._tool_factories: Optional[AgentToolFactories] = tool_factories
        # 这几个句柄在配置缺失时保持 None，运行期用 getattr/真值判断兜底，
        # 因此声明为 Any 而不是 Optional[Any]，否则每次成员访问都会被判为可能为 None
        self.llm: Any = None
        self.agent: Any = None
        self.agent_executor: Any = None
        self.intent_router: Any = None
        self.all_tools: list[Any] = []
        self.model_name: str = ""
        self._api_key: str = ""
        self._base_url: str = ""
        self._timeout: int = 30
        # 聊天上下文预算，初始化配置后按 agent 配置覆盖
        self._context_budget: ContextBudgetConfig = ContextBudgetConfig()

        self._initialize_llm_service()

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

    @staticmethod
    def _resolve_context_prompt_tokens(system_prompt: str, message: str) -> int:
        """估算系统提示词与用户提示词占用的 token"""
        return estimate_tokens(system_prompt) + estimate_tokens(message)

    @staticmethod
    def _compose_direct_system_message(summary: str) -> str:
        """闲聊路径把历史摘要并入系统消息"""
        if not summary:
            return Messages.GENERIC_CHAT_MESSAGE
        return (
            Messages.GENERIC_CHAT_MESSAGE + Messages.CHAT_MEMORY_SUMMARY_HEADER()
        ) + summary

    async def _build_direct_messages(
        self,
        message: str,
        user_id: Optional[int],
        db: Optional[AsyncSession],
        runnable_config: Optional[dict] = None,
        notes: Optional[list[str]] = None,
    ) -> list[Any]:
        """构建直连对话的消息列表

        直连路径统一从这里组装，流式与非流式、Agent 就绪与降级场景保持一致，
        历史记忆按上下文预算加载并裁剪，系统身份不读取记忆

        Args:
            message: 本轮用户提问
            user_id: 归一化后的用户 ID
            db: 数据库会话
            runnable_config: LangChain RunnableConfig
            notes: 记忆压缩说明的收集列表，供前端思考流与历史记录复用

        Returns:
            list[Any]: 系统消息、历史消息与本轮提问
        """
        summary = ""
        chat_history: list[ChatHistoryItem] = []
        if db and user_id is not None and is_memory_user(user_id):
            summary, chat_history = await self._load_chat_memory(
                user_id,
                message,
                Messages.GENERIC_CHAT_MESSAGE,
                db,
                False,
                runnable_config,
                notes,
            )
        elif user_id is not None:
            Logger.info(Messages.MEMORY_SKIPPED_SYSTEM_USER(user_id))

        history_messages: list[Any] = []
        for human_msg, ai_msg in chat_history:
            history_messages.append(HumanMessage(content=human_msg))
            history_messages.append(AIMessage(content=ai_msg))

        return [
            SystemMessage(content=self._compose_direct_system_message(summary)),
            *history_messages,
            HumanMessage(content=message),
        ]

    async def _load_agent_memory(
        self,
        user_id: Optional[int],
        message: str,
        db: Optional[AsyncSession],
        runnable_config: Optional[dict] = None,
        notes: Optional[list[str]] = None,
    ) -> tuple[str, list[ChatHistoryItem]]:
        """加载 Agent 路径的聊天记忆

        Agent 路径的系统提示词更长且需要绑定工具，单独走带工具预留的预算，
        系统身份不读取记忆

        Args:
            user_id: 归一化后的用户 ID
            message: 本轮用户提问
            db: 数据库会话
            runnable_config: LangChain RunnableConfig
            notes: 记忆压缩说明的收集列表，供前端思考流与历史记录复用

        Returns:
            tuple[str, list[ChatHistoryItem]]: 历史摘要与注入的原文轮次
        """
        if not (db and user_id is not None and is_memory_user(user_id)):
            if user_id is not None:
                Logger.info(Messages.MEMORY_SKIPPED_SYSTEM_USER(user_id))
            return "", []

        return await self._load_chat_memory(
            user_id,
            message,
            Prompts.AGENT_PROMPT(),
            db,
            True,
            runnable_config,
            notes,
        )

    async def _load_memory_summary(
        self, user_id: int, db: AsyncSession
    ) -> Optional[AiUserSummary]:
        """读取用户级记忆摘要，读取失败时降级为无摘要"""
        try:
            return await self.ai_summary_mapper.get_by_user_id_async(db, user_id)
        except Exception as error:
            Logger.error(Messages.LLM_CHAT_MEMORY_LOAD_FAILED(error))
            return None

    async def _load_chat_memory(
        self,
        user_id: int,
        message: str,
        system_prompt: str,
        db: AsyncSession,
        use_tools: bool,
        runnable_config: Optional[dict] = None,
        notes: Optional[list[str]] = None,
    ) -> tuple[str, list[ChatHistoryItem]]:
        """加载用户级聊天记忆，必要时压缩并持久化

        历史预算由模型窗口扣除提示词、输出预留与工具预留后推导；
        未超过阈值时按原样注入，超过或接近阈值时把更早轮次折叠进摘要；
        折叠内容按单次输入上限分批，未纳入批次的记录留在原表，下一轮继续折叠

        Args:
            user_id: 真实用户 ID
            message: 本轮用户提问
            system_prompt: 当前路径使用的系统提示词
            db: 数据库会话
            use_tools: 是否走带工具的 Agent 路径
            runnable_config: LangChain RunnableConfig，使压缩调用进入同一链路追踪
            notes: 记忆压缩说明的收集列表，压缩发生时写入一条说明

        Returns:
            tuple[str, list[ChatHistoryItem]]: 历史摘要与注入的原文轮次
        """
        summary_row = await self._load_memory_summary(user_id, db)
        # 模型沿用 SQLAlchemy 旧式 Column 标注，字段静态类型是 Column[T]，取值时按运行期值处理
        summary_values: Any = summary_row
        watermark = (
            int(summary_values.last_summarized_history_id or 0) if summary_row else 0
        )
        existing_summary = str(summary_values.summary or "") if summary_row else ""
        summarized_count = (
            int(summary_values.summarized_count or 0) if summary_row else 0
        )
        candidate_rounds = self._context_budget.candidate_rounds

        try:
            histories = await self.ai_history_mapper.get_ai_history_after_id_async(
                db, user_id, watermark, candidate_rounds
            )
        except Exception as error:
            # 历史读取失败只降级为无原文，不打断本轮回答
            Logger.error(Messages.LLM_CHAT_HISTORY_LOAD_FAILED(error))
            return existing_summary, []

        # 达到候选上限说明水位线之后还有更早的记录被本轮查询越过
        limit_reached = len(histories) == candidate_rounds
        if limit_reached:
            Logger.warning(
                Messages.LLM_CHAT_MEMORY_CANDIDATE_LIMIT_REACHED(
                    self.service_name, candidate_rounds
                )
            )

        records: list[tuple[int, str, str]] = [
            (int(row.id), str(row.ask), str(row.reply)) for row in histories
        ]
        prompt_tokens = self._resolve_context_prompt_tokens(system_prompt, message)
        plan = plan_chat_context(
            existing_summary,
            [(ask, reply) for _history_id, ask, reply in records],
            self._context_budget,
            prompt_tokens,
            use_tools,
        )
        Logger.info(
            Messages.LLM_CHAT_MEMORY_PLANNED(
                self.service_name,
                plan.budget_tokens,
                plan.estimated_tokens,
                len(plan.history),
                len(plan.compact_targets),
            )
        )
        if plan.budget_tokens <= 0:
            # 窗口已被提示词与预留占满，本轮既不注入历史也不压缩，优先保证请求可用
            Logger.warning(
                Messages.LLM_CHAT_CONTEXT_BUDGET_EXHAUSTED(
                    self.service_name,
                    self._context_budget.window_tokens,
                    self._context_budget.reserved_tokens(prompt_tokens, use_tools),
                )
            )
            return "", []

        targets = await self._resolve_compact_targets(
            db, user_id, watermark, records, plan, limit_reached
        )
        if not targets:
            return plan.summary, plan.history

        batch = plan_compact_batch(targets, self._context_budget)
        if not batch.rounds:
            return plan.summary, plan.history

        new_summary = await self._compact_chat_memory(
            existing_summary=existing_summary,
            targets=batch.rounds,
            watermark_id=batch.last_id,
            summarized_count=summarized_count + batch.count,
            db=db,
            user_id=user_id,
            runnable_config=runnable_config,
            notes=notes,
        )
        if new_summary is None:
            return plan.summary, plan.history

        # 摘要长度可能变化，按新摘要重新收敛一次注入窗口，保证不超预算
        replanned = plan_chat_context(
            new_summary, plan.history, self._context_budget, prompt_tokens, use_tools
        )
        return new_summary, replanned.history

    async def _resolve_compact_targets(
        self,
        db: AsyncSession,
        user_id: int,
        watermark: int,
        records: list[tuple[int, str, str]],
        plan: ContextPlan,
        limit_reached: bool,
    ) -> list[tuple[int, str, str]]:
        """解析本轮待折叠的记录，按旧到新排列

        命中候选上限时，水位线与本轮最近记录之间存在被查询跳过的更早记录，
        这部分必须一并补进摘要，否则会随着水位线推进被永久排除在记忆之外

        Args:
            db: 数据库会话
            user_id: 真实用户 ID
            watermark: 当前压缩水位线
            records: 本轮读取到的记录，按旧到新排列
            plan: 上下文组装方案
            limit_reached: 本轮是否命中候选轮数上限

        Returns:
            list[tuple[int, str, str]]: 待折叠记录，无可折叠内容时为空
        """
        targets: list[tuple[int, str, str]] = []
        if limit_reached and records:
            targets.extend(
                await self._load_gap_records(db, user_id, watermark, records[0][0])
            )
        # compact_targets 恒为 records 的前缀，按下标取回对应的记录 id
        targets.extend(records[: len(plan.compact_targets)])
        return targets

    async def _load_gap_records(
        self, db: AsyncSession, user_id: int, watermark: int, oldest_loaded_id: int
    ) -> list[tuple[int, str, str]]:
        """读取水位线之后、本轮最近记录之前被候选上限跳过的更早记录

        读取失败时降级为空，本轮压缩照常进行，跳过的部分留待下一轮补折叠
        """
        try:
            rows = await self.ai_history_mapper.get_oldest_ai_history_after_id_async(
                db, user_id, watermark, self._context_budget.candidate_rounds
            )
        except Exception as error:
            Logger.error(Messages.LLM_CHAT_HISTORY_LOAD_FAILED(error))
            return []

        return [
            (int(row.id), str(row.ask), str(row.reply))
            for row in rows
            if int(row.id) < oldest_loaded_id
        ]

    async def _compact_chat_memory(
        self,
        existing_summary: str,
        targets: list[ChatHistoryItem],
        watermark_id: int,
        summarized_count: int,
        db: AsyncSession,
        user_id: int,
        runnable_config: Optional[dict] = None,
        notes: Optional[list[str]] = None,
    ) -> Optional[str]:
        """把更早轮次折叠进摘要并持久化

        压缩失败时返回 None，调用方保持原摘要且不推进水位线，
        下一轮可重新尝试，不会造成历史丢失；
        传入 notes 时写入一条说明，供前端思考流与历史记录展示这次整理

        Returns:
            Optional[str]: 合并后的摘要，失败时返回 None
        """
        Logger.info(
            Messages.LLM_CHAT_MEMORY_COMPACT_START(
                self.service_name, len(targets), watermark_id
            )
        )
        try:
            new_content = "\n".join(
                Messages.CHAT_HISTORY_LINE(ask, reply) for ask, reply in targets
            )
            prompt = Prompts.USER_MEMORY_COMPACT(
                existing_summary or Messages.CHAT_MEMORY_EMPTY_SUMMARY,
                new_content,
                self._context_budget.summary_max_chars,
            )
            messages = [
                SystemMessage(content=Messages.CHAT_MEMORY_COMPACT_SYSTEM_MESSAGE),
                HumanMessage(content=prompt),
            ]

            response = await self.llm.ainvoke(
                messages,
                config=self._build_compact_runnable_config(
                    runnable_config, len(targets)
                ),
            )
            new_summary = str(response.content or "").strip()
            if not new_summary:
                raise ValueError(Messages.CHAT_MEMORY_COMPACT_EMPTY_RESULT)
            # 超限摘要不落库也不截断，保留旧摘要并保持水位线，下一轮重新合并
            if len(new_summary) > self._context_budget.summary_max_chars:
                Logger.warning(
                    Messages.LLM_CHAT_MEMORY_COMPACT_OVER_LIMIT(
                        self.service_name,
                        len(new_summary),
                        self._context_budget.summary_max_chars,
                    )
                )
                self._append_compact_note(
                    notes, Messages.CHAT_MEMORY_COMPACT_FAILED_THINKING(len(targets))
                )
                return None

            await self.ai_summary_mapper.upsert_async(
                db, user_id, new_summary, watermark_id, summarized_count
            )
            Logger.info(
                Messages.LLM_CHAT_MEMORY_COMPACT_COMPLETED(
                    self.service_name, len(new_summary), watermark_id
                )
            )
            self._append_compact_note(
                notes,
                Messages.CHAT_MEMORY_COMPACT_THINKING(len(targets), len(new_summary)),
            )
            return new_summary
        except Exception as error:
            Logger.error(
                Messages.LLM_CHAT_MEMORY_COMPACT_FAILED(self.service_name, error)
            )
            self._append_compact_note(
                notes, Messages.CHAT_MEMORY_COMPACT_FAILED_THINKING(len(targets))
            )
            return None

    @staticmethod
    def _append_compact_note(notes: Optional[list[str]], note: str) -> None:
        """记录一条记忆压缩说明，未传入收集列表时不做任何事"""
        if notes is None:
            return
        notes.append(note)

    @staticmethod
    def _build_notes_frames(notes: list[str]) -> list[dict[str, str]]:
        """把记忆压缩说明转为思考帧，供流式接口下发给前端"""
        return [{"type": "thinking", "content": note} for note in notes]

    @staticmethod
    def _build_compact_runnable_config(
        runnable_config: Optional[dict], folded_rounds: int
    ) -> dict:
        """构建记忆压缩调用的运行配置

        压缩是一次额外的模型调用，沿用调用方配置才能挂进同一条链路，
        同时单独命名并记录折叠轮数，便于在追踪中区分它与业务问答

        Args:
            runnable_config: 调用方传入的 LangChain RunnableConfig
            folded_rounds: 本次折叠的轮数

        Returns:
            dict: 用于压缩调用的 RunnableConfig
        """
        config = dict(runnable_config) if runnable_config else {}
        config["run_name"] = "chat.memory.compact"
        # metadata 重建而非原地更新，避免改动调用方持有的字典
        config["metadata"] = {
            **(config.get("metadata") or {}),
            "memory_compact_rounds": folded_rounds,
        }
        return config

    def _build_complete_thinking_text(
        self, intermediate_steps: list[IntermediateStep], final_result: str = ""
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
            thinking_parts.append(Messages.AGENT_EXECUTION_PROCESS_HEADER())
            for i, (action, observation) in enumerate(intermediate_steps, 1):
                tool_name = action.tool if hasattr(action, "tool") else str(action)
                tool_input = action.tool_input if hasattr(action, "tool_input") else ""

                step_text = Messages.AGENT_EXECUTION_STEP(
                    i, tool_name, str(tool_input), str(observation)
                )

                thinking_parts.append(step_text)

        # 添加最终结果
        if final_result:
            thinking_parts.append(Messages.AGENT_FINAL_RESULT(final_result))

        # 拼接所有部分
        complete_text = "".join(thinking_parts)
        return complete_text

    def _build_chat_context(
        self, summary: str, chat_history: list[ChatHistoryItem]
    ) -> str:
        """构建聊天历史上下文

        历史已在加载阶段按上下文预算与摘要水位线处理，这里直接拼接；
        摘要排在原文之前，保证更早的结论不会因窗口裁剪而丢失

        Args:
            summary: 用户级历史摘要，可为空
            chat_history: 已裁剪的聊天历史列表

        Returns:
            str: 格式化的历史对话上下文
        """
        parts: list[str] = []
        if summary:
            parts.append(Messages.CHAT_MEMORY_SUMMARY_HEADER() + summary)
        if chat_history:
            parts.append(
                "\n\n历史对话:\n"
                + "\n".join(
                    Messages.CHAT_HISTORY_LINE(ask, reply)
                    for ask, reply in chat_history
                )
            )
        if not parts:
            return ""
        return "".join(parts) + "\n\n"

    def _normalize_user_id(self, user_id: Any) -> Optional[int]:
        """将用户ID统一转换为整数，避免不同调用链传入字符串"""
        normalized = normalize_user_id(user_id)
        if normalized is None and user_id is not None:
            Logger.warning(Messages.LLM_INVALID_USER_ID(user_id))
        return normalized

    @staticmethod
    def _extract_message_content(content: Any) -> str:
        """兼容字符串和内容块，提取可展示的正文"""
        if content is None:
            return ""
        if hasattr(content, "content"):
            message_content = BaseAiService._extract_message_content(content.content)
            if message_content:
                return message_content
            additional_kwargs = getattr(content, "additional_kwargs", {}) or {}
            for key in ("content", "text"):
                extra_content = BaseAiService._extract_message_content(
                    additional_kwargs.get(key)
                )
                if extra_content:
                    return extra_content
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts: list[str] = []
            for block in content:
                if isinstance(block, str):
                    text_parts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(str(block.get("text") or ""))
            return "".join(text_parts)
        return str(content)

    def _final_stream_options(self) -> dict[str, Any]:
        """获取最终答案流式输出参数"""
        if self.service_name == "GLM":
            return {
                "extra_body": {
                    "thinking": {
                        "type": "enabled",
                        "reasoning_effort": "low",
                    }
                }
            }
        return {}

    def _build_agent_fallback_result(
        self, intermediate_steps: list[IntermediateStep]
    ) -> str:
        """从 Agent 工具结果构建非空兜底回答"""
        for _, observation in reversed(intermediate_steps):
            observation_text = self._extract_message_content(observation)
            if observation_text.strip():
                return observation_text
        return Messages.MESSAGE_RETRIEVAL_ERROR

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

    def _build_llm_client_options(self, service_cfg: dict[str, Any]) -> dict[str, Any]:
        """构建模型客户端的模型级扩展参数

        推理强度配置与模型键同前缀，如 gpt_model_name 对应 gpt_reasoning_effort
        推理模型在 /v1/chat/completions 下绑定 function tools 时必须为 none
        否则模型会返回 reasoning_effort 相关的 400 错误
        未配置时不下发该参数，交由模型默认行为决定

        Args:
            service_cfg: 模型服务配置

        Returns:
            dict[str, Any]: 传入 ChatOpenAI 的扩展参数
        """
        model_key_prefix = self.model_config_key.removesuffix("_model_name")
        reasoning_effort = str(
            service_cfg.get(f"{model_key_prefix}_reasoning_effort") or ""
        ).strip()
        if not reasoning_effort:
            return {}
        return {"reasoning_effort": reasoning_effort}

    def _initialize_agent_stack(self, max_iterations: int = 5) -> None:
        """初始化工具、意图路由器和 Agent"""
        try:
            _, _, _, self.all_tools = initialize_ai_tools(
                tool_factories=self._tool_factories
            )
            self.intent_router = IntentRouter(
                self.llm,
                use_structured_output=self.use_structured_output,
            )

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

    def _initialize_llm_service(self) -> None:
        """从配置中初始化 CloseAI 客户端和 Agent 能力"""
        try:
            service_cfg: dict[str, Any] = (load_config("agent") or {}).get(
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
            self._context_budget = ContextBudgetConfig.from_agent_config(service_cfg)

            if self._api_key and self._base_url and self.model_name:
                self.llm = ChatOpenAI(
                    model=self.model_name,
                    api_key=SecretStr(self._api_key),
                    base_url=self._base_url,
                    temperature=self.temperature,
                    timeout=self._timeout,
                    **self._build_llm_client_options(service_cfg),
                )
                self._initialize_agent_stack(max_iterations=agent_max_iterations)
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
            Logger.info(
                Messages.BASIC_CHAT_REPLY_LENGTH(self.service_name, len(result))
            )
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
            Logger.info(
                Messages.REFERENCE_CHAT_REPLY_LENGTH(self.service_name, len(result))
            )
            return result

        except Exception as error:
            Logger.error(
                Messages.REFERENCE_CHAT_EXCEPTION(self.service_name, str(error))
            )
            return Messages.CHAT_SERVICE_ERROR(error)

    async def summarize_content(self, content: str, max_length: int = 1000) -> str:
        """总结长文本内容"""
        try:
            Logger.info(Messages.SUMMARIZE_START(self.service_name, len(content)))

            if not getattr(self, "llm", None):
                return Messages.INITIALIZATION_ERROR

            prompt = self._get_summarize_prompt(content, max_length)
            messages = [
                SystemMessage(content=Messages.SUMMARIZE_CHAT_MESSAGE),
                HumanMessage(content=prompt),
            ]

            response = await self.llm.ainvoke(messages)
            result: str = response.content[:max_length]
            Logger.info(Messages.SUMMARIZE_COMPLETED(self.service_name, len(result)))
            return result

        except Exception as error:
            Logger.error(Messages.SUMMARIZE_EXCEPTION(self.service_name, str(error)))
            return Messages.SUMMARIZE_SERVICE_ERROR(error)

    async def simple_chat(
        self,
        message: str,
        user_id: int | str = 0,
        db: Optional[AsyncSession] = None,
        runnable_config: Optional[dict] = None,
        notes: Optional[list[str]] = None,
    ) -> str:
        """普通聊天接口

        Args:
            message: 用户消息
            user_id: 用户ID
            db: 数据库会话
            runnable_config: LangChain RunnableConfig (用于 LangSmith 追踪传播)
            notes: 记忆压缩说明的收集列表，调用方据此落库历史记录的思考字段
        """
        try:
            normalized_user_id = self._normalize_user_id(user_id)
            Logger.info(Messages.USER_SEND_MESSAGE(user_id, message))

            if not getattr(self, "llm", None):
                return Messages.INITIALIZATION_ERROR

            if not self.agent_executor:
                # Agent 不可用时降级为直连对话，与流式路径一致地带上历史记忆
                config = dict(runnable_config) if runnable_config else {}
                config.setdefault("run_name", "chat.direct")
                messages = await self._build_direct_messages(
                    message, normalized_user_id, db, config, notes
                )
                response = await self.llm.ainvoke(messages, config=config)
                result: str = response.content
                Logger.info(Messages.CHAT_REPLY_LENGTH(self.service_name, len(result)))
                return result

            intent = "general_chat"
            intent_resolution = "default_fallback"
            if self.intent_router and db and normalized_user_id is not None:
                (
                    intent,
                    has_permission,
                    permission_msg,
                    intent_resolution,
                ) = await self.intent_router.route_with_permission_check_async(
                    message, normalized_user_id, db, runnable_config
                )
                Logger.info(Messages.INTENT_WITH_PERMISSION(intent, has_permission))

                if not has_permission:
                    Logger.info(Messages.USER_NO_PERMISSION_FOR_INTENT(user_id, intent))
                    return permission_msg or Messages.NO_PERMISSION_ERROR
            elif self.intent_router:
                intent, intent_resolution = await self.intent_router.route_async(
                    message
                )
                Logger.info(Messages.INTENT_RECOGNIZED(intent))

            # 将意图信息补充到 runnable_config 中
            config = dict(runnable_config) if runnable_config else {}
            config.setdefault("metadata", {})
            config["metadata"].update(
                {
                    "intent": intent,
                    "intent_resolution": intent_resolution,
                }
            )

            direct_chat = is_direct_chat_intent(intent)
            if direct_chat:
                config.setdefault("run_name", "chat.direct")
                messages = await self._build_direct_messages(
                    message, normalized_user_id, db, config, notes
                )
                response = await self.llm.ainvoke(messages, config=config)
                result = response.content
            else:
                Logger.info(Messages.AGENT_PROCESSING_MESSAGE)
                config.setdefault("run_name", "agent.execute")

                # 用户身份经 contextvars（ToolScope）随请求传递给工具层，
                # 单例工具不再持有可变用户字段

                summary, chat_history = await self._load_agent_memory(
                    normalized_user_id, message, db, config, notes
                )
                context = self._build_chat_context(summary, chat_history)
                user_info = (
                    Messages.CURRENT_USER_ID_INFO(normalized_user_id)
                    if normalized_user_id is not None
                    and is_memory_user(normalized_user_id)
                    else ""
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
        db: Optional[AsyncSession] = None,
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
            # 记忆压缩说明先以思考帧下发，让前端知道本轮在回答前整理过历史
            notes: list[str] = []

            if not getattr(self, "llm", None):
                yield {"type": "error", "content": Messages.INITIALIZATION_ERROR}
                return

            if not self.agent_executor:
                config = dict(runnable_config) if runnable_config else {}
                config.setdefault("run_name", "chat.direct")
                messages = await self._build_direct_messages(
                    message, normalized_user_id, db, config, notes
                )
                for frame in self._build_notes_frames(notes):
                    yield frame

                try:
                    async for chunk in self.llm.astream(
                        messages,
                        config=config,
                        **self._final_stream_options(),
                    ):
                        try:
                            chunk_content = self._extract_message_content(chunk)
                            if chunk_content:
                                Logger.debug(
                                    Messages.STREAM_CHUNK_RECEIVED_LENGTH(
                                        len(chunk_content)
                                    )
                                )
                                yield {"type": "content", "content": chunk_content}
                        except Exception as chunk_error:
                            Logger.error(
                                Messages.STREAM_CHUNK_EXCEPTION(str(chunk_error))
                            )
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
                    message, normalized_user_id, db, runnable_config
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
                intent, intent_resolution = await self.intent_router.route_async(
                    message
                )
                Logger.info(Messages.INTENT_RECOGNIZED(intent))

            # 将意图信息补充到 runnable_config 中
            config = dict(runnable_config) if runnable_config else {}
            config.setdefault("metadata", {})
            config["metadata"].update(
                {
                    "intent": intent,
                    "intent_resolution": intent_resolution,
                }
            )

            direct_chat = is_direct_chat_intent(intent)
            if direct_chat:
                config.setdefault("run_name", "chat.direct")
                messages = await self._build_direct_messages(
                    message, normalized_user_id, db, config, notes
                )
                for frame in self._build_notes_frames(notes):
                    yield frame

                try:
                    async for chunk in self.llm.astream(
                        messages,
                        config=config,
                        **self._final_stream_options(),
                    ):
                        try:
                            chunk_content = self._extract_message_content(chunk)
                            if chunk_content:
                                yield {"type": "content", "content": chunk_content}
                        except Exception as chunk_error:
                            Logger.error(
                                Messages.STREAM_CHUNK_EXCEPTION(str(chunk_error))
                            )
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

                # 用户身份经 contextvars（ToolScope）随请求传递给工具层，
                # 单例工具不再持有可变用户字段

                summary, chat_history = await self._load_agent_memory(
                    normalized_user_id, message, db, config, notes
                )
                for frame in self._build_notes_frames(notes):
                    yield frame
                context = self._build_chat_context(summary, chat_history)
                user_info = (
                    Messages.CURRENT_USER_ID_INFO(normalized_user_id)
                    if normalized_user_id is not None
                    and is_memory_user(normalized_user_id)
                    else ""
                )
                full_input = context + user_info + Messages.CURRENT_QUESTION(message)

                Logger.info(Messages.AGENT_START_PROCESSING_MESSAGE)

                # 事件流驱动的中间结果，工具步骤完成即推送思考片段
                intermediate_steps: list[IntermediateStep] = []
                agent_result: str = ""
                # run_id 关联工具事件，保证并行工具调用也能正确回填步骤
                pending_tool_runs: dict[str, tuple[str, Any]] = {}
                step_counter: int = 0
                thinking_header_sent: bool = False

                try:
                    async for event in self.agent_executor.astream_events(
                        {
                            "input": full_input,
                            "system_message": Messages.STREAMING_CHAT_THINKING_SYSTEM_MESSAGE,
                        },
                        config=config,
                        version="v2",
                    ):
                        event_name = str(event.get("event") or "")
                        event_data: dict[str, Any] = event.get("data") or {}

                        if event_name == "on_tool_start":
                            if not thinking_header_sent:
                                thinking_header_sent = True
                                yield {
                                    "type": "thinking",
                                    "content": Messages.AGENT_EXECUTION_PROCESS_HEADER(),
                                }

                            step_counter += 1
                            tool_name = str(event.get("name") or "")
                            tool_input = event_data.get("input", "")
                            pending_tool_runs[str(event.get("run_id"))] = (
                                tool_name,
                                tool_input,
                            )
                            yield {
                                "type": "thinking",
                                "content": Messages.AGENT_EXECUTION_STEP_START(
                                    step_counter, tool_name, str(tool_input)
                                ),
                            }
                            continue

                        if event_name == "on_tool_end":
                            tool_name, tool_input = pending_tool_runs.pop(
                                str(event.get("run_id")),
                                (str(event.get("name") or ""), ""),
                            )
                            observation = event_data.get("output", "")
                            intermediate_steps.append(
                                (
                                    AgentAction(
                                        tool=tool_name, tool_input=tool_input, log=""
                                    ),
                                    observation,
                                )
                            )
                            yield {
                                "type": "thinking",
                                "content": Messages.AGENT_EXECUTION_STEP_RESULT(
                                    self._extract_message_content(observation)
                                ),
                            }
                            continue

                        if event_name == "on_chain_end":
                            chain_output = event_data.get("output")
                            if (
                                isinstance(chain_output, dict)
                                and "output" in chain_output
                            ):
                                agent_result = (
                                    self._extract_message_content(
                                        chain_output.get("output")
                                    )
                                    or agent_result
                                )
                                collected_steps = chain_output.get("intermediate_steps")
                                if (
                                    isinstance(collected_steps, list)
                                    and collected_steps
                                ):
                                    intermediate_steps = collected_steps
                except Exception as agent_error:
                    error_msg = str(agent_error)
                    Logger.error(Messages.AGENT_EXECUTION_FAILED(error_msg))
                    yield {
                        "type": "content",
                        "content": self._resolve_service_error_message(error_msg),
                    }
                    return

                # 事件流未携带最终结果时，从工具观测值兜底
                agent_result = agent_result or self._build_agent_fallback_result(
                    intermediate_steps
                )

                thinking_text = self._build_complete_thinking_text(
                    intermediate_steps, agent_result
                )

                Logger.info(Messages.THINKING_PROCESS_LENGTH(len(thinking_text)))
                if len(thinking_text) > 5000:
                    Logger.debug(
                        Messages.THINKING_PROCESS_PREVIEW_TEXT(thinking_text[:2000])
                    )
                    Logger.debug(
                        Messages.THINKING_PROCESS_MIDDLE_TEXT(
                            thinking_text[
                                len(thinking_text) // 2 - 1000 : len(thinking_text) // 2
                                + 1000
                            ]
                        )
                    )
                    Logger.debug(
                        Messages.THINKING_PROCESS_END_TEXT(thinking_text[-2000:])
                    )
                else:
                    Logger.debug(Messages.COMPLETE_THINKING_PROCESS_TEXT(thinking_text))

                yield {
                    "type": "thinking",
                    "content": Messages.AGENT_FINAL_RESULT(agent_result),
                }

                Logger.info(Messages.AGENT_START_STREAMING_MESSAGE)

                history_messages = []
                for human_msg, ai_msg in chat_history:
                    history_messages.append(HumanMessage(content=human_msg))
                    history_messages.append(AIMessage(content=ai_msg))

                stream_messages = [
                    SystemMessage(content=Messages.GENERIC_CHAT_MESSAGE),
                    *history_messages,
                    HumanMessage(
                        content=(Messages.STREAM_FINAL_PROMPT(message, agent_result))
                    ),
                ]

                # 在 try 之前初始化，避免异常路径下变量被判为可能未绑定
                final_content_emitted = False
                try:
                    async for chunk in self.llm.astream(
                        stream_messages,
                        config=config,
                        **self._final_stream_options(),
                    ):
                        try:
                            chunk_content = self._extract_message_content(chunk)
                            if chunk_content:
                                final_content_emitted = True
                                yield {"type": "content", "content": chunk_content}
                        except Exception as chunk_error:
                            Logger.error(
                                Messages.STREAM_CHUNK_EXCEPTION(str(chunk_error))
                            )
                            continue
                except Exception as final_stream_error:
                    error_msg = str(final_stream_error)
                    Logger.error(Messages.FINAL_STREAM_OUTPUT_FAILED(error_msg))
                    yield {
                        "type": "content",
                        "content": self._resolve_service_error_message(error_msg),
                    }
                if not final_content_emitted:
                    Logger.warning(Messages.FINAL_STREAM_EMPTY_FALLBACK)
                    try:
                        fallback_response = await self.llm.ainvoke(
                            stream_messages,
                            config=config,
                            **self._final_stream_options(),
                        )
                        fallback_content = self._extract_message_content(
                            fallback_response
                        )
                    except Exception as fallback_error:
                        Logger.error(
                            Messages.FINAL_STREAM_OUTPUT_FAILED(str(fallback_error))
                        )
                        fallback_content = ""

                    fallback_content = (
                        fallback_content
                        or agent_result
                        or self._build_agent_fallback_result(intermediate_steps)
                    )
                    yield {
                        "type": "content",
                        "content": fallback_content,
                    }

        except Exception as error:
            Logger.error(Messages.STREAM_CHAT_EXCEPTION(str(error)))
            yield {
                "type": "error",
                "content": self._resolve_service_error_message(str(error)),
            }
