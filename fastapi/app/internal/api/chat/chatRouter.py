import datetime
import json
import time
import uuid
from contextlib import aclosing
from typing import Any, AsyncGenerator, Dict, Optional

from app.common.decorators import log, requireInternalToken
from app.common.middleware import get_current_user_id
from app.internal.agents.langsmith import (
    build_chat_metadata,
    build_chat_tags,
    get_langsmith_context,
    get_langsmith_context_async,
)
from app.core.base import Logger, success
from app.core.config import load_config
from app.core.constants import HttpCode, Messages
from app.core.db import get_db
from app.internal.models import AiHistory
from app.internal.schemas import (
    AIServiceType,
    ChatRequest,
    ChatResponse,
    ChatResponseData,
)
from app.internal.services import (
    AiHistoryService,
    DeepseekService,
    GeminiService,
    GptService,
    get_ai_history_service,
    get_deepseek_service,
    get_gemini_service,
    get_gpt_service,
)
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, Request

router: APIRouter = APIRouter(
    prefix="/chat",
    tags=["AI聊天模块"],
)


def _resolve_model_info(service: AIServiceType) -> dict:
    """解析当前服务对应的模型信息，用于 LangSmith metadata"""
    server_config = load_config("server") or {}
    deployment_env = server_config.get("mode", "dev")
    agent_cfg = (load_config("agent") or {}).get("closeai", {})

    model_map = {
        AIServiceType.GPT: ("gpt", agent_cfg.get("gpt_model_name", "")),
        AIServiceType.GEMINI: ("gemini", agent_cfg.get("gemini_model_name", "")),
        AIServiceType.DEEPSEEK: ("deepseek", agent_cfg.get("deepseek_model_name", "")),
    }
    provider, model_name = model_map.get(service, ("unknown", ""))
    return {
        "provider": provider,
        "model_name": model_name,
        "deployment_env": str(deployment_env),
    }


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
    db: AsyncSession = Depends(get_db),
    gptService: GptService = Depends(get_gpt_service),
    geminiService: GeminiService = Depends(get_gemini_service),
    deepseekService: DeepseekService = Depends(get_deepseek_service),
    aiHistoryService: AiHistoryService = Depends(get_ai_history_service),
) -> JSONResponse:
    """普通发送聊天消息"""

    user_id: str = get_current_user_id() or ""
    # 使用实际用户ID替代请求中的 user_id
    actual_user_id: str = user_id or "1"
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
            try:
                runnable_config = {
                    "run_name": "chat.direct",
                    "tags": langsmith_tags,
                    "metadata": langsmith_metadata,
                }
            except Exception:
                pass

        # 根据请求的服务类型选择对应的AI服务
        if request.service == AIServiceType.GPT:
            Logger.info(Messages.CHAT_SERVICE_PROCESSING("GPT", actual_user_id, False))
            response_message: str = await gptService.simple_chat(
                message=request.message,
                user_id=actual_user_id,
                db=db,
                runnable_config=runnable_config,
            )
        elif request.service == AIServiceType.GEMINI:
            Logger.info(Messages.CHAT_SERVICE_PROCESSING("Gemini", actual_user_id, False))
            response_message = await geminiService.simple_chat(
                message=request.message,
                user_id=actual_user_id,
                db=db,
                runnable_config=runnable_config,
            )
        else:
            Logger.info(Messages.CHAT_SERVICE_PROCESSING("DeepSeek", actual_user_id, False))
            response_message = await deepseekService.simple_chat(
                message=request.message,
                user_id=actual_user_id,
                db=db,
                runnable_config=runnable_config,
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

    # 保存AI历史记录
    history = AiHistory(
        user_id=int(actual_user_id),
        ask=request.message,
        reply=response_message,
        thinking=None,
        ai_type=request.service.value,
    )
    await aiHistoryService.create_ai_history(history, db)
    Logger.info(Messages.AI_HISTORY_SAVED(actual_user_id, request.service.value, False))

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
    response_model=ChatResponse,
    summary="流式聊天",
    description="流式发送聊天消息并返回响应",
)
@log("流式聊天")
async def stream_message(
    http_request: Request,
    request: ChatRequest,
    gptService: GptService = Depends(get_gpt_service),
    geminiService: GeminiService = Depends(get_gemini_service),
    deepseekService: DeepseekService = Depends(get_deepseek_service),
    aiHistoryService: AiHistoryService = Depends(get_ai_history_service),
) -> StreamingResponse:
    """流式发送聊天消息"""

    user_id: str = get_current_user_id() or ""
    actual_user_id: str = user_id or "1"
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
        async with get_langsmith_context_async(
            name="chat.stream",
            tags=langsmith_tags,
            metadata=langsmith_metadata,
        ):
            # 在 event_generator 内部创建 db session，确保流式处理完成后立即释放
            async with aclosing(get_db()) as db_generator:
                db = await anext(db_generator)
                # 根据请求的服务类型选择对应的AI服务
                if request.service == AIServiceType.GPT:
                    Logger.info(Messages.CHAT_SERVICE_PROCESSING("GPT", actual_user_id, True))
                    stream_generator: AsyncGenerator[Any, None] = (
                        gptService.stream_chat(
                            message=request.message,
                            user_id=actual_user_id,
                            db=db,
                            runnable_config=runnable_config,
                        )
                    )
                elif request.service == AIServiceType.GEMINI:
                    Logger.info(Messages.CHAT_SERVICE_PROCESSING("Gemini", actual_user_id, True))
                    stream_generator = geminiService.stream_chat(
                        message=request.message,
                        user_id=actual_user_id,
                        db=db,
                        runnable_config=runnable_config,
                    )
                else:
                    Logger.info(Messages.CHAT_SERVICE_PROCESSING("DeepSeek", actual_user_id, True))
                    stream_generator = deepseekService.stream_chat(
                        message=request.message,
                        user_id=actual_user_id,
                        db=db,
                        runnable_config=runnable_config,
                    )

                async for chunk in stream_generator:
                    # 解析流式数据块中的消息类型
                    # 格式: {"type": "thinking|content|error", "content": "..."}
                    if isinstance(chunk, dict):
                        chunk_type = chunk.get("type", "content")
                        chunk_content = chunk.get("content", "")
                    else:
                        # 如果是字符串，默认为 content 类型
                        chunk_type = "content"
                        chunk_content = str(chunk)

                    # 记录chunk长度（用于调试）
                    Logger.debug(
                        Messages.STREAM_CHUNK_RECEIVED(chunk_type, len(chunk_content))
                    )

                    # 分别累积思考过程和最终内容
                    if chunk_type == "thinking":
                        thinking_acc += chunk_content
                    elif chunk_type == "content":
                        message_acc += chunk_content

                    # 构建响应数据 - 确保chunk_content完整输出
                    data: Dict[str, Any] = success(
                        {
                            "message": message_acc,
                            "conversation_id": conversation_id,
                            "chat_id": chat_id,
                            "user_id": actual_user_id,
                            "timestamp": int(time.time()),
                            "service": request.service.value,
                            "message_type": chunk_type,
                            "chunk": chunk_content,
                        }
                    )
                    # 使用 ensure_ascii=False 保证 UTF-8 编码，avoid_json_tricks 保证完整性
                    json_str: str = json.dumps(
                        data.model_dump(), ensure_ascii=False, separators=(",", ":")
                    )
                    Logger.debug(Messages.SSE_PACKET_SIZE(len(json_str)))
                    yield f"data: {json_str}\n\n"

                # 流式聊天完成后保存AI历史记录（在完成流式传输后）
                if message_acc:
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

                if not message_acc:
                    data = success(
                        {
                            "message": "",
                            "conversation_id": conversation_id,
                            "chat_id": chat_id,
                            "user_id": actual_user_id,
                            "timestamp": int(time.time()),
                            "service": request.service.value,
                            "message_type": "done",
                            "chunk": "",
                        }
                    )
                    yield (
                        "data: "
                        + json.dumps(
                            data.model_dump(), ensure_ascii=False, separators=(",", ":")
                        )
                        + "\n\n"
                    )

    return StreamingResponse(event_generator(), media_type="text/event-stream")
