import datetime
import time
import uuid
from collections.abc import AsyncGenerator, Mapping
from contextlib import aclosing, suppress
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base import (
    Logger,
    LoggerProtocol,
    StreamFrameContext,
    build_native_frame,
    build_openai_chunk_frame,
    build_openai_done_frame,
    build_openai_error_frame,
    build_openai_finish_frame,
    build_openai_start_frame,
)
from app.core.config import load_config
from app.core.constants import Defaults, Messages
from app.core.db import get_db
from app.core.middleware import get_current_user_id
from app.internal.agents import (
    build_chat_metadata,
    build_chat_tags,
    get_langsmith_context,
    get_langsmith_context_async,
)
from app.internal.schemas import (
    AIServiceType,
    ChatRequest,
    ChatResponseData,
    ChatStreamRequest,
    StreamFormat,
)

from .chatService import persist_chat_history, select_chat_model


@dataclass(frozen=True)
class ChatSession:
    """一次聊天会话的上下文数据，含用户、会话 ID 与 LangSmith 追踪标签元数据"""

    user_id: str
    conversation_id: str
    chat_id: str
    frame_context: StreamFrameContext
    tags: list[str]
    metadata: Optional[dict[str, Any]]


@dataclass(frozen=True)
class ChatStreamEvent:
    """单个流式聊天事件，kind 区分正文、思考或错误等消息类型"""

    kind: str
    content: str


class ChatApplicationService:
    """装配模型调用、追踪和历史保存的聊天用例"""

    def __init__(
        self,
        models: Mapping[AIServiceType, Any],
        history_service: Any,
        logger: LoggerProtocol | None = None,
    ) -> None:
        """注入各模型服务映射、AI 历史服务与日志器"""
        self._models = models
        self._history_service = history_service
        # 日志器可注入，缺省回退全局单例
        self._logger: LoggerProtocol = logger or Logger

    def _prepare(self, request: ChatRequest, streaming: bool) -> ChatSession:
        """构建聊天会话上下文：解析用户身份（缺省回退系统用户）、生成会话与请求 ID，组装 LangSmith 标签元数据和 SSE 帧上下文"""
        current_user_id: Optional[int] = get_current_user_id()
        if current_user_id is None:
            self._logger.warning(
                Messages.USER_IDENTITY_FALLBACK_TO_SYSTEM(
                    "stream_message" if streaming else "send_message"
                )
            )
        user_id = (
            str(current_user_id)
            if current_user_id is not None
            else str(Defaults.SYSTEM_USER_ID)
        )
        conversation_id = request.conversationId or (
            f"{user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        )
        chat_id = f"chat_{uuid.uuid4().hex[:12]}"
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        server_config = load_config("server") or {}
        agent_config = (load_config("agent") or {}).get("closeai", {})
        model_names = {
            AIServiceType.GPT: ("gpt", agent_config["gpt_model_name"]),
            AIServiceType.GEMINI: ("gemini", agent_config["gemini_model_name"]),
            AIServiceType.GLM: ("glm", agent_config["glm_model_name"]),
            AIServiceType.DEEPSEEK: ("deepseek", agent_config["deepseek_model_name"]),
            AIServiceType.CLAUDE: ("claude", agent_config["claude_model_name"]),
            AIServiceType.QWEN: ("qwen", agent_config["qwen_model_name"]),
        }
        provider, model_name = model_names[request.service]
        deployment_env = str(server_config["mode"])
        tags = build_chat_tags(
            env=deployment_env,
            route="chat_stream" if streaming else "chat_send",
            model_provider=provider,
            mode="agent",
            streaming=streaming,
            rag_enabled=getattr(request, "rag_enabled", False),
        )
        metadata = build_chat_metadata(
            request_id=request_id,
            user_id=user_id,
            conversation_id=conversation_id,
            model_provider=provider,
            model_name=model_name,
            streaming=streaming,
            agent_mode=True,
            rag_enabled=getattr(request, "rag_enabled", False),
            deployment_env=deployment_env,
        )
        frame_context = StreamFrameContext(
            conversation_id=conversation_id,
            chat_id=chat_id,
            user_id=user_id,
            service=request.service.value,
            model=model_name,
            completion_id=f"{Defaults.STREAM_OPENAI_COMPLETION_ID_PREFIX}{uuid.uuid4().hex[:12]}",
            created=int(time.time()),
        )
        return ChatSession(
            user_id, conversation_id, chat_id, frame_context, tags, metadata
        )

    async def send(self, request: ChatRequest, db: AsyncSession) -> ChatResponseData:
        """同步聊天：按请求类型选定模型调用 simple_chat 获取完整回复，保存历史并返回响应数据"""
        session = self._prepare(request, streaming=False)
        with get_langsmith_context(
            name="chat.send", tags=session.tags, metadata=session.metadata
        ) as root_run:
            runnable_config: Optional[dict[str, Any]] = None
            if root_run is not None:
                with suppress(Exception):
                    runnable_config = {
                        "run_name": "chat.direct",
                        "tags": session.tags,
                        "metadata": session.metadata,
                    }
            notes: list[str] = []
            model = select_chat_model(request.service, self._models)
            self._logger.info(
                Messages.CHAT_SERVICE_PROCESSING(
                    request.service.value, session.user_id, False
                )
            )
            response_message: str = await model.simple_chat(
                message=request.message,
                user_id=session.user_id,
                db=db,
                runnable_config=runnable_config,
                notes=notes,
                raise_on_error=True,
            )

        saved = await persist_chat_history(
            self._history_service,
            db,
            session.user_id,
            request.message,
            response_message,
            "".join(notes),
            request.service,
        )
        if saved:
            self._logger.info(
                Messages.AI_HISTORY_SAVED(session.user_id, request.service.value, False)
            )
        else:
            self._logger.info(
                Messages.AI_HISTORY_SKIPPED_SYSTEM_USER(session.user_id, False)
            )
        return ChatResponseData(
            message=response_message,
            conversationId=session.conversation_id,
            chatId=session.chat_id,
            userId=session.user_id,
            timestamp=int(time.time()),
        )

    def stream(
        self, request: ChatStreamRequest
    ) -> tuple[StreamFrameContext, AsyncGenerator[ChatStreamEvent, None]]:
        """流式聊天：返回 SSE 帧上下文与事件生成器，逐块区分思考和正文并累积，结束后保存聊天历史"""
        session = self._prepare(request, streaming=True)

        async def generate() -> AsyncGenerator[ChatStreamEvent, None]:
            """stream 内嵌的异步生成器，逐块转发模型流式输出并在结束时持久化聊天历史"""
            message_acc = ""
            thinking_acc = ""
            runnable_config = {
                "run_name": "chat.direct",
                "tags": session.tags,
                "metadata": session.metadata,
            }
            async with (
                get_langsmith_context_async(
                    name="chat.stream", tags=session.tags, metadata=session.metadata
                ),
                aclosing(get_db()) as db_generator,
            ):
                db = await anext(db_generator)
                model = select_chat_model(request.service, self._models)
                self._logger.info(
                    Messages.CHAT_SERVICE_PROCESSING(
                        request.service.value, session.user_id, True
                    )
                )
                async for chunk in model.stream_chat(
                    message=request.message,
                    user_id=session.user_id,
                    db=db,
                    runnable_config=runnable_config,
                ):
                    if isinstance(chunk, dict):
                        kind = chunk.get("type", Defaults.STREAM_TYPE_CONTENT)
                        content = chunk.get("content", "")
                    else:
                        kind = Defaults.STREAM_TYPE_CONTENT
                        content = str(chunk)
                    self._logger.debug(
                        Messages.STREAM_CHUNK_RECEIVED(kind, len(content))
                    )
                    if kind == Defaults.STREAM_TYPE_THINKING:
                        thinking_acc += content
                    elif kind == Defaults.STREAM_TYPE_CONTENT:
                        message_acc += content
                    yield ChatStreamEvent(kind, content)

                if message_acc:
                    saved = await persist_chat_history(
                        self._history_service,
                        db,
                        session.user_id,
                        request.message,
                        message_acc,
                        thinking_acc,
                        request.service,
                    )
                    if saved:
                        self._logger.info(
                            Messages.AI_HISTORY_SAVED(
                                session.user_id, request.service.value, True
                            )
                        )
                    else:
                        self._logger.info(
                            Messages.AI_HISTORY_SKIPPED_SYSTEM_USER(
                                session.user_id, True
                            )
                        )

        return session.frame_context, generate()

    def stream_frames(self, request: ChatStreamRequest) -> AsyncGenerator[str, None]:
        """执行流式聊天并返回请求指定格式的 SSE 帧"""
        context, events = self.stream(request)
        return self.format_stream(
            context, events, request.streamFormat == StreamFormat.OPENAI
        )

    @staticmethod
    async def format_stream(
        context: StreamFrameContext,
        events: AsyncGenerator[ChatStreamEvent, None],
        openai_format: bool,
    ) -> AsyncGenerator[str, None]:
        """将聊天事件转换为项目或 OpenAI 兼容的 SSE 帧"""
        accumulated_message = ""
        if openai_format:
            yield build_openai_start_frame(context)

        async with aclosing(events):
            async for event in events:
                if event.kind == Defaults.STREAM_TYPE_CONTENT:
                    accumulated_message += event.content
                if openai_format:
                    if not event.content:
                        continue
                    if event.kind == Defaults.STREAM_TYPE_ERROR:
                        yield build_openai_error_frame(message=event.content)
                    else:
                        yield build_openai_chunk_frame(
                            context=context, chunk_type=event.kind, chunk=event.content
                        )
                    continue

                frame = build_native_frame(
                    accumulated_message=accumulated_message,
                    message_type=event.kind,
                    chunk=event.content,
                    context=context,
                )
                Logger.debug(Messages.SSE_PACKET_SIZE(len(frame)))
                yield frame

        if openai_format:
            yield build_openai_finish_frame(context)
            yield build_openai_done_frame()
        elif not accumulated_message:
            yield build_native_frame(
                accumulated_message="",
                message_type=Defaults.STREAM_TYPE_DONE,
                chunk="",
                context=context,
            )


@lru_cache
def get_chat_application_service(
    gpt_service: Any,
    gemini_service: Any,
    glm_service: Any,
    deepseek_service: Any,
    claude_service: Any,
    qwen_service: Any,
    history_service: Any,
    logger: LoggerProtocol | None = None,
) -> ChatApplicationService:
    """将六个模型服务装配为按类型索引的模型映射并缓存 ChatApplicationService 单例"""
    return ChatApplicationService(
        {
            AIServiceType.GPT: gpt_service,
            AIServiceType.GEMINI: gemini_service,
            AIServiceType.GLM: glm_service,
            AIServiceType.DEEPSEEK: deepseek_service,
            AIServiceType.CLAUDE: claude_service,
            AIServiceType.QWEN: qwen_service,
        },
        history_service,
        logger,
    )
