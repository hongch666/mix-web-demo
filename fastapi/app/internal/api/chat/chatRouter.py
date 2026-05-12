import datetime
import json
import time
import uuid
from contextlib import aclosing
from typing import Any, AsyncGenerator, Dict

from app.common.decorators import log, requireInternalToken
from app.common.middleware import get_current_user_id
from app.core.base import HttpCode, Logger, success
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
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Request

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
    db: Session = Depends(get_db),
    gptService: GptService = Depends(get_gpt_service),
    geminiService: GeminiService = Depends(get_gemini_service),
    deepseekService: DeepseekService = Depends(get_deepseek_service),
    aiHistoryService: AiHistoryService = Depends(get_ai_history_service),
) -> JSONResponse:
    """普通发送聊天消息"""

    user_id: str = get_current_user_id() or ""
    # 使用实际用户ID替代请求中的user_id
    actual_user_id: str = user_id or "1"

    # 根据请求的服务类型选择对应的AI服务
    if request.service == AIServiceType.GPT:
        Logger.info(f"使用GPT服务处理用户 {actual_user_id} 的请求")
        response_message: str = await gptService.simple_chat(
            message=request.message, user_id=actual_user_id, db=db
        )
    elif request.service == AIServiceType.GEMINI:
        Logger.info(f"使用Gemini服务处理用户 {actual_user_id} 的请求")
        response_message = await geminiService.simple_chat(
            message=request.message, user_id=actual_user_id, db=db
        )
    else:
        Logger.info(f"使用DeepSeek服务处理用户 {actual_user_id} 的请求")
        response_message = await deepseekService.simple_chat(
            message=request.message, user_id=actual_user_id, db=db
        )

    # 生成会话ID（如果没有提供）
    conversation_id: str = (
        request.conversation_id
        or f"{actual_user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    )
    chat_id: str = f"chat_{uuid.uuid4().hex[:12]}"

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
    Logger.info(
        f"AI历史记录已保存: user_id={actual_user_id}, ai_type={request.service.value}"
    )

    # 成功响应 - 按照success格式
    response_data: ChatResponseData = ChatResponseData(
        message=response_message,
        conversation_id=conversation_id,
        chat_id=chat_id,
        user_id=actual_user_id,
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
    conversation_id: str = (
        request.conversation_id
        or f"{actual_user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    )
    chat_id: str = f"chat_{uuid.uuid4().hex[:12]}"

    async def event_generator() -> AsyncGenerator[str, None]:
        message_acc: str = ""
        thinking_acc: str = ""
        # 在 event_generator 内部创建 db session，确保流式处理完成后立即释放
        async with aclosing(get_db()) as db_generator:
            db = await anext(db_generator)
            # 根据请求的服务类型选择对应的AI服务
            if request.service == AIServiceType.GPT:
                Logger.info(f"使用GPT流式服务处理用户 {actual_user_id} 的请求")
                stream_generator: AsyncGenerator[Any, None] = gptService.stream_chat(
                    message=request.message, user_id=actual_user_id, db=db
                )
            elif request.service == AIServiceType.GEMINI:
                Logger.info(f"使用Gemini流式服务处理用户 {actual_user_id} 的请求")
                stream_generator = geminiService.stream_chat(
                    message=request.message, user_id=actual_user_id, db=db
                )
            else:
                Logger.info(f"使用DeepSeek流式服务处理用户 {actual_user_id} 的请求")
                stream_generator = deepseekService.stream_chat(
                    message=request.message, user_id=actual_user_id, db=db
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
                    f"流式块类型: {chunk_type}, 块内容长度: {len(chunk_content)}"
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
                    data, ensure_ascii=False, separators=(",", ":")
                )
                Logger.debug(f"SSE 数据包大小: {len(json_str)} 字节")
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
                    f"流式AI历史记录已保存: user_id={actual_user_id}, ai_type={request.service.value}"
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
                    + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
                    + "\n\n"
                )

    return StreamingResponse(event_generator(), media_type="text/event-stream")
