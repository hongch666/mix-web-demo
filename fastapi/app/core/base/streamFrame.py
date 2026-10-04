import json
import time
from dataclasses import dataclass
from typing import Any

from app.core.base import success
from app.core.constants import Defaults


@dataclass(frozen=True)
class StreamFrameContext:
    """流式帧的公共上下文

    一次流式请求内不变，native 与 openai 两种格式共用
    """

    conversation_id: str
    chat_id: str
    user_id: str
    service: str
    model: str
    completion_id: str
    created: int


def _to_sse_frame(payload: dict[str, Any]) -> str:
    """把响应体序列化成一条 SSE 帧"""
    body: str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f"data: {body}\n\n"


def _openai_payload(
    context: StreamFrameContext,
    delta: dict[str, Any],
    finish_reason: str | None,
) -> dict[str, Any]:
    """构造 OpenAI Chat Completions 分片的公共结构"""
    return {
        "id": context.completion_id,
        "object": Defaults.STREAM_OPENAI_CHUNK_OBJECT,
        "created": context.created,
        "model": context.model,
        # 标准客户端会忽略扩展字段，这里保留会话信息便于排查
        "conversation_id": context.conversation_id,
        "chat_id": context.chat_id,
        "choices": [
            {
                "index": 0,
                "delta": delta,
                "finish_reason": finish_reason,
            }
        ],
    }


def build_native_frame(
    *,
    accumulated_message: str,
    message_type: str,
    chunk: str,
    context: StreamFrameContext,
) -> str:
    """构造项目自定义流式帧（前端契约）

    message 为累计正文，chunk 为当前帧增量，message_type 区分 thinking/content/error/done
    """
    response: Any = success(
        {
            "message": accumulated_message,
            "conversation_id": context.conversation_id,
            "chat_id": context.chat_id,
            "user_id": context.user_id,
            "timestamp": int(time.time()),
            "service": context.service,
            "message_type": message_type,
            "chunk": chunk,
        }
    )
    return _to_sse_frame(response.model_dump())


def build_openai_start_frame(context: StreamFrameContext) -> str:
    """构造 OpenAI 兼容的首帧，声明 assistant 角色"""
    return _to_sse_frame(
        _openai_payload(
            context,
            {"role": Defaults.STREAM_OPENAI_ASSISTANT_ROLE},
            None,
        )
    )


def build_openai_chunk_frame(
    *,
    context: StreamFrameContext,
    chunk_type: str,
    chunk: str,
) -> str:
    """构造 OpenAI 兼容的内容分片帧

    思考走 reasoning_content，正文走 content，两者在标准客户端里分列展示
    """
    if chunk_type == Defaults.STREAM_TYPE_THINKING:
        delta: dict[str, Any] = {"reasoning_content": chunk}
    else:
        delta = {"content": chunk}
    return _to_sse_frame(_openai_payload(context, delta, None))


def build_openai_error_frame(*, message: str) -> str:
    """构造 OpenAI 风格的错误帧"""
    return _to_sse_frame({"error": {"message": message}})


def build_openai_finish_frame(context: StreamFrameContext) -> str:
    """构造 OpenAI 兼容的结束帧"""
    return _to_sse_frame(
        _openai_payload(context, {}, Defaults.STREAM_OPENAI_FINISH_REASON_STOP)
    )


def build_openai_done_frame() -> str:
    """构造 OpenAI 兼容流的结束标记"""
    return f"data: {Defaults.STREAM_DONE_SENTINEL}\n\n"
