from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.core.base import ApiResponse, success
from app.core.constants import SwaggerConfig
from app.core.decorators import log
from app.dependencies import ChatApplicationServiceDep, ChatServiceDep, DbSession
from app.internal.schemas import (
    ChatRequest,
    ChatResponse,
    ChatResponseData,
    ChatStreamRequest,
    OpenAIStreamChunk,
)

router: APIRouter = APIRouter(
    prefix="/chat",
    tags=["AI聊天模块"],
)


@router.get(
    "/models",
    response_model=ApiResponse[list[str]],
    summary="获取聊天模型列表",
    description=(
        "返回当前支持的聊天模型枚举值列表，元素即聊天请求 service 参数的合法取值，"
        "供前端渲染模型选择项"
    ),
)
@log("获取聊天模型列表")
async def get_chat_models(chat_service: ChatServiceDep) -> ApiResponse:
    """获取聊天模型列表"""

    return success(data=chat_service.get_available_models())


@router.post(
    "/send",
    response_model=ChatResponse,
    summary="普通聊天",
    description="发送聊天消息并返回响应",
)
@log("普通聊天")
async def send_message(
    http_request: Request,
    request: ChatRequest,
    db: DbSession,
    chat_service: ChatApplicationServiceDep,
) -> ApiResponse[ChatResponseData]:
    """普通发送聊天消息"""
    return success(await chat_service.send(request, db))


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
    chat_service: ChatApplicationServiceDep,
) -> StreamingResponse:
    """流式发送聊天消息"""
    return StreamingResponse(
        chat_service.stream_frames(request),
        media_type="text/event-stream",
    )
