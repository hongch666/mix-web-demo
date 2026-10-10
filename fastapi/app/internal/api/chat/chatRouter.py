import datetime
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import aclosing, suppress
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.common.decorators import log, requireInternalToken
from app.common.middleware import get_current_user_id
from app.core.auth import is_memory_user
from app.core.base import (
    ApiResponse,
    Logger,
    StreamFrameContext,
    build_native_frame,
    build_openai_chunk_frame,
    build_openai_done_frame,
    build_openai_error_frame,
    build_openai_finish_frame,
    build_openai_start_frame,
    success,
)
from app.core.config import load_config
from app.core.constants import Defaults, HttpCode, Messages, SwaggerConfig
from app.core.db import get_db
from app.dependencies import (
    AiHistoryServiceDep,
    DbSession,
    GeminiServiceDep,
    GlmServiceDep,
    GptServiceDep,
)
from app.internal.agents.langsmith import (
    build_chat_metadata,
    build_chat_tags,
    get_langsmith_context,
    get_langsmith_context_async,
)
from app.internal.models import AiHistory
from app.internal.schemas import (
    AIServiceType,
    ChatRequest,
    ChatResponse,
    ChatResponseData,
    ChatStreamRequest,
    OpenAIStreamChunk,
    StreamFormat,
)

router: APIRouter = APIRouter(
    prefix="/chat",
    tags=["AI聊天模块"],
)


@router.post(
    "/send",
    response_model=ChatResponse,
    summary="普通聊天",
    description="发送聊天消息并返回响应",
)
@log("普通聊天")
@requireInternalToken
async def send_message(
    http_request: Request,
    request: ChatRequest,
    db: DbSession,
    gptService: GptServiceDep,
    geminiService: GeminiServiceDep,
    glmService: GlmServiceDep,
    aiHistoryService: AiHistoryServiceDep,
) -> ChatResponse | ApiResponse[ChatResponseData]:
    """普通发送聊天消息"""

    user_id: Optional[int] = get_current_user_id()
    # 使用实际用户ID替代请求中的 user_id，身份缺失时按系统调用处理
    if user_id is None:
        Logger.warning(Messages.USER_IDENTITY_FALLBACK_TO_SYSTEM("send_message"))
    actual_user_id: str = _resolve_system_user_id()
    request_id: str = f"req_{uuid.uuid4().hex[:12]}"

    # 生成会话ID（如果没有提供）
    conversation_id: str = (
        request.conversationId
        or f"{actual_user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    )
    chat_id: str = f"chat_{uuid.uuid4().hex[:12]}"

    # 解析模型信息用于 LangSmith
    model_info = _resolve_model_info(request.service)

    # 构建 LangSmith tags 和 metadata
    langsmith_tags = build_chat_tags(
        env=model_info["deployment_env"],
        route="chat_send",
        model_provider=model_info["provider"],
        mode="agent",
        streaming=False,
        rag_enabled=getattr(request, "rag_enabled", False),
    )
    langsmith_metadata = build_chat_metadata(
        request_id=request_id,
        user_id=actual_user_id,
        conversation_id=conversation_id,
        model_provider=model_info["provider"],
        model_name=model_info["model_name"],
        streaming=False,
        agent_mode=True,
        rag_enabled=getattr(request, "rag_enabled", False),
        deployment_env=model_info["deployment_env"],
    )

    # LangSmith 根 Trace 上下文
    with get_langsmith_context(
        name="chat.send",
        tags=langsmith_tags,
        metadata=langsmith_metadata,
    ) as root_run:
        # 构建 RunnableConfig 用于传递给 LangChain
        runnable_config: Optional[dict] = None
        if root_run is not None:
            # 组装 LangChain 运行配置失败不影响主流程，仅降级为 None
            with suppress(Exception):
                runnable_config = {
                    "run_name": "chat.direct",
                    "tags": langsmith_tags,
                    "metadata": langsmith_metadata,
                }

        # 根据请求的服务类型选择对应的AI服务
        # 记忆压缩说明由服务层写入 compact_notes，供历史记录的思考字段落库
        compact_notes: list[str] = []
        if request.service == AIServiceType.GPT:
            Logger.info(Messages.CHAT_SERVICE_PROCESSING("GPT", actual_user_id, False))
            response_message: str = await gptService.simple_chat(
                message=request.message,
                user_id=actual_user_id,
                db=db,
                runnable_config=runnable_config,
                notes=compact_notes,
            )
        elif request.service == AIServiceType.GEMINI:
            Logger.info(
                Messages.CHAT_SERVICE_PROCESSING("Gemini", actual_user_id, False)
            )
            response_message = await geminiService.simple_chat(
                message=request.message,
                user_id=actual_user_id,
                db=db,
                runnable_config=runnable_config,
                notes=compact_notes,
            )
        else:
            Logger.info(Messages.CHAT_SERVICE_PROCESSING("GLM", actual_user_id, False))
            response_message = await glmService.simple_chat(
                message=request.message,
                user_id=actual_user_id,
                db=db,
                runnable_config=runnable_config,
                notes=compact_notes,
            )

    # 检查是否有错误
    if (
        "异常" in response_message
        or "错误" in response_message
        or "失败" in response_message
    ):
        return ChatResponse(
            code=HttpCode.INTERNAL_SERVER_ERROR, data=None, msg=response_message
        )

    # 保存AI历史记录，系统调用身份不写入记忆
    if is_memory_user(actual_user_id):
        history = AiHistory(
            user_id=int(actual_user_id),
            ask=request.message,
            reply=response_message,
            thinking="".join(compact_notes) or None,
            ai_type=request.service.value,
        )
        await aiHistoryService.create_ai_history(history, db)
        Logger.info(
            Messages.AI_HISTORY_SAVED(actual_user_id, request.service.value, False)
        )
    else:
        Logger.info(Messages.AI_HISTORY_SKIPPED_SYSTEM_USER(actual_user_id, False))

    # 成功响应 - 按照success格式
    response_data: ChatResponseData = ChatResponseData(
        message=response_message,
        conversationId=conversation_id,
        chatId=chat_id,
        userId=actual_user_id,
        timestamp=int(time.time()),
    )
    return success(response_data)


@router.post(
    "/stream",
    response_model=ChatResponse | OpenAIStreamChunk,
    summary="流式聊天",
    description=(
        "流式发送聊天消息并返回逐帧响应。streamFormat 可选：native（默认，项目自定义帧，"
        "含累计 message、chunk 与 message_type，供前端按思考/正文分别渲染）；"
        "openai（OpenAI Chat Completions 兼容分片，思考走 delta.reasoning_content，"
        "正文走 delta.content，末尾返回 [DONE]，便于 Apifox 等标准客户端实时自动合并）"
    ),
    responses=SwaggerConfig.STREAM_CHAT_RESPONSES,
)
@log("流式聊天")
async def stream_message(
    http_request: Request,
    request: ChatStreamRequest,
    gptService: GptServiceDep,
    geminiService: GeminiServiceDep,
    glmService: GlmServiceDep,
    aiHistoryService: AiHistoryServiceDep,
) -> StreamingResponse:
    """流式发送聊天消息"""

    user_id: Optional[int] = get_current_user_id()
    # 身份缺失时按系统调用处理，与 send_message 保持一致
    if user_id is None:
        Logger.warning(Messages.USER_IDENTITY_FALLBACK_TO_SYSTEM("stream_message"))
    actual_user_id: str = _resolve_system_user_id()
    request_id: str = f"req_{uuid.uuid4().hex[:12]}"
    conversation_id: str = (
        request.conversationId
        or f"{actual_user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    )
    chat_id: str = f"chat_{uuid.uuid4().hex[:12]}"

    # 解析模型信息用于 LangSmith
    model_info = _resolve_model_info(request.service)

    # 构建 LangSmith tags 和 metadata
    langsmith_tags = build_chat_tags(
        env=model_info["deployment_env"],
        route="chat_stream",
        model_provider=model_info["provider"],
        mode="agent",
        streaming=True,
        rag_enabled=getattr(request, "rag_enabled", False),
    )
    langsmith_metadata = build_chat_metadata(
        request_id=request_id,
        user_id=actual_user_id,
        conversation_id=conversation_id,
        model_provider=model_info["provider"],
        model_name=model_info["model_name"],
        streaming=True,
        agent_mode=True,
        rag_enabled=getattr(request, "rag_enabled", False),
        deployment_env=model_info["deployment_env"],
    )

    # 流式帧上下文，两种帧格式共用；openai 格式额外需要 completion_id/created/model
    frame_context: StreamFrameContext = StreamFrameContext(
        conversation_id=conversation_id,
        chat_id=chat_id,
        user_id=actual_user_id,
        service=request.service.value,
        model=model_info["model_name"],
        completion_id=(
            f"{Defaults.STREAM_OPENAI_COMPLETION_ID_PREFIX}{uuid.uuid4().hex[:12]}"
        ),
        created=int(time.time()),
    )
    use_openai_format: bool = request.streamFormat == StreamFormat.OPENAI

    async def event_generator() -> AsyncGenerator[str, None]:
        message_acc: str = ""
        thinking_acc: str = ""

        # 构建 RunnableConfig 用于传递给 LangChain
        runnable_config: Optional[dict] = {
            "run_name": "chat.direct",
            "tags": langsmith_tags,
            "metadata": langsmith_metadata,
        }

        # LangSmith 根 Trace 在生成器内持有，确保 SSE 完成/异常/断连均收尾
        # 两层上下文职责不同（Trace 生命周期 / DB session 生命周期），保留分层写法
        async with get_langsmith_context_async(  # noqa: SIM117
            name="chat.stream",
            tags=langsmith_tags,
            metadata=langsmith_metadata,
        ):
            # 在 event_generator 内部创建 db session，确保流式处理完成后立即释放
            async with aclosing(get_db()) as db_generator:
                db = await anext(db_generator)
                # 根据请求的服务类型选择对应的AI服务
                if request.service == AIServiceType.GPT:
                    Logger.info(
                        Messages.CHAT_SERVICE_PROCESSING("GPT", actual_user_id, True)
                    )
                    stream_generator: AsyncGenerator[Any, None] = (
                        gptService.stream_chat(
                            message=request.message,
                            user_id=actual_user_id,
                            db=db,
                            runnable_config=runnable_config,
                        )
                    )
                elif request.service == AIServiceType.GEMINI:
                    Logger.info(
                        Messages.CHAT_SERVICE_PROCESSING("Gemini", actual_user_id, True)
                    )
                    stream_generator = geminiService.stream_chat(
                        message=request.message,
                        user_id=actual_user_id,
                        db=db,
                        runnable_config=runnable_config,
                    )
                else:
                    Logger.info(
                        Messages.CHAT_SERVICE_PROCESSING("GLM", actual_user_id, True)
                    )
                    stream_generator = glmService.stream_chat(
                        message=request.message,
                        user_id=actual_user_id,
                        db=db,
                        runnable_config=runnable_config,
                    )

                if use_openai_format:
                    # 先声明 assistant 角色，标准客户端据此初始化消息
                    yield build_openai_start_frame(frame_context)

                async for chunk in stream_generator:
                    # 解析流式数据块中的消息类型
                    # 格式: {"type": "thinking|content|error", "content": "..."}
                    if isinstance(chunk, dict):
                        chunk_type = chunk.get("type", Defaults.STREAM_TYPE_CONTENT)
                        chunk_content = chunk.get("content", "")
                    else:
                        # 如果是字符串，默认为 content 类型
                        chunk_type = Defaults.STREAM_TYPE_CONTENT
                        chunk_content = str(chunk)

                    # 记录chunk长度（用于调试）
                    Logger.debug(
                        Messages.STREAM_CHUNK_RECEIVED(chunk_type, len(chunk_content))
                    )

                    # 分别累积思考过程和最终内容，落库与输出格式无关
                    if chunk_type == Defaults.STREAM_TYPE_THINKING:
                        thinking_acc += chunk_content
                    elif chunk_type == Defaults.STREAM_TYPE_CONTENT:
                        message_acc += chunk_content

                    if use_openai_format:
                        # openai 格式只发内容分片，空分片跳过，错误单独成帧
                        if not chunk_content:
                            continue
                        if chunk_type == Defaults.STREAM_TYPE_ERROR:
                            yield build_openai_error_frame(message=chunk_content)
                        else:
                            yield build_openai_chunk_frame(
                                context=frame_context,
                                chunk_type=chunk_type,
                                chunk=chunk_content,
                            )
                        continue

                    # 前端契约格式 - 确保chunk_content完整输出
                    frame: str = build_native_frame(
                        accumulated_message=message_acc,
                        message_type=chunk_type,
                        chunk=chunk_content,
                        context=frame_context,
                    )
                    Logger.debug(Messages.SSE_PACKET_SIZE(len(frame)))
                    yield frame

                # 流式聊天完成后保存AI历史记录（在完成流式传输后）
                # 系统调用身份不写入记忆，避免所有匿名请求共用同一个记忆桶
                if message_acc and is_memory_user(actual_user_id):
                    history = AiHistory(
                        user_id=int(actual_user_id),
                        ask=request.message,
                        reply=message_acc,
                        thinking=thinking_acc if thinking_acc else None,
                        ai_type=request.service.value,
                    )
                    await aiHistoryService.create_ai_history(history, db)
                    Logger.info(
                        Messages.AI_HISTORY_SAVED(
                            actual_user_id, request.service.value, True
                        )
                    )
                elif message_acc:
                    Logger.info(
                        Messages.AI_HISTORY_SKIPPED_SYSTEM_USER(actual_user_id, True)
                    )

                if use_openai_format:
                    yield build_openai_finish_frame(frame_context)
                    yield build_openai_done_frame()
                elif not message_acc:
                    # 前端契约：正文为空时补一帧结束标记
                    yield build_native_frame(
                        accumulated_message="",
                        message_type=Defaults.STREAM_TYPE_DONE,
                        chunk="",
                        context=frame_context,
                    )

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _resolve_system_user_id() -> str:
    """身份缺失时返回系统调用身份，供允许匿名访问的聊天接口使用"""
    user_id: Optional[int] = get_current_user_id()
    return str(user_id) if user_id is not None else str(Defaults.SYSTEM_USER_ID)


def _resolve_model_info(service: AIServiceType) -> dict:
    """解析当前服务对应的模型信息，用于 LangSmith metadata"""
    server_config = load_config("server") or {}
    deployment_env = server_config["mode"]
    agent_cfg = (load_config("agent") or {}).get("closeai", {})

    model_map = {
        AIServiceType.GPT: ("gpt", agent_cfg["gpt_model_name"]),
        AIServiceType.GEMINI: ("gemini", agent_cfg["gemini_model_name"]),
        AIServiceType.GLM: ("glm", agent_cfg["glm_model_name"]),
    }
    provider, model_name = model_map.get(service, ("unknown", ""))
    return {
        "provider": provider,
        "model_name": model_name,
        "deployment_env": str(deployment_env),
    }
