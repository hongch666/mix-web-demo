"""流式帧构造的单元测试"""

import json
from typing import Any

from app.core.base import (
    StreamFrameContext,
    build_native_frame,
    build_openai_chunk_frame,
    build_openai_done_frame,
    build_openai_error_frame,
    build_openai_finish_frame,
    build_openai_start_frame,
)
from app.core.constants import Defaults


def _context() -> StreamFrameContext:
    return StreamFrameContext(
        conversation_id="c1",
        chat_id="chat_1",
        user_id="122",
        service="GPT",
        model="gpt-6-luna",
        completion_id="chatcmpl-abc123",
        created=1730000000,
    )


def _payload(frame: str) -> dict[str, Any]:
    """取出 SSE 帧的 JSON 载荷"""
    assert frame.startswith("data: ")
    assert frame.endswith("\n\n")
    return json.loads(frame.removeprefix("data: ").strip())


# native 帧保留前端契约字段：累计 message、chunk 与 message_type
def test_build_native_frame_keeps_frontend_contract() -> None:
    frame = build_native_frame(
        accumulated_message="你好",
        message_type=Defaults.STREAM_TYPE_CONTENT,
        chunk="你",
        context=_context(),
    )

    payload = _payload(frame)

    assert payload["code"] == 200
    assert payload["data"]["message"] == "你好"
    assert payload["data"]["chunk"] == "你"
    assert payload["data"]["message_type"] == Defaults.STREAM_TYPE_CONTENT
    assert payload["data"]["conversation_id"] == "c1"
    assert payload["data"]["chat_id"] == "chat_1"
    assert payload["data"]["user_id"] == "122"
    assert payload["data"]["service"] == "GPT"


# openai 首帧声明 assistant 角色并带上标准元信息
def test_build_openai_start_frame_declares_assistant_role() -> None:
    payload = _payload(build_openai_start_frame(_context()))
    choice = payload["choices"][0]

    assert choice["delta"] == {"role": Defaults.STREAM_OPENAI_ASSISTANT_ROLE}
    assert choice["finish_reason"] is None
    assert payload["id"] == "chatcmpl-abc123"
    assert payload["object"] == Defaults.STREAM_OPENAI_CHUNK_OBJECT
    assert payload["created"] == 1730000000
    assert payload["model"] == "gpt-6-luna"
    assert payload["conversation_id"] == "c1"


# openai 思考分片走 reasoning_content，正文分片走 content，两者不混
def test_build_openai_chunk_frame_splits_thinking_and_content() -> None:
    thinking = _payload(
        build_openai_chunk_frame(
            context=_context(),
            chunk_type=Defaults.STREAM_TYPE_THINKING,
            chunk="先查一下",
        )
    )
    content = _payload(
        build_openai_chunk_frame(
            context=_context(),
            chunk_type=Defaults.STREAM_TYPE_CONTENT,
            chunk="共 5 个用户",
        )
    )

    assert thinking["choices"][0]["delta"] == {"reasoning_content": "先查一下"}
    assert content["choices"][0]["delta"] == {"content": "共 5 个用户"}
    assert "content" not in thinking["choices"][0]["delta"]


# openai 结束帧的 finish_reason 为 stop 且 delta 为空
def test_build_openai_finish_frame_marks_stop() -> None:
    payload = _payload(build_openai_finish_frame(_context()))
    choice = payload["choices"][0]

    assert choice["delta"] == {}
    assert choice["finish_reason"] == Defaults.STREAM_OPENAI_FINISH_REASON_STOP


# openai 错误帧使用 error.message 结构
def test_build_openai_error_frame_uses_error_message() -> None:
    payload = _payload(build_openai_error_frame(message="模型不可用"))

    assert payload == {"error": {"message": "模型不可用"}}


# openai 流以 [DONE] 标记结束
def test_build_openai_done_frame_returns_sentinel() -> None:
    assert build_openai_done_frame() == f"data: {Defaults.STREAM_DONE_SENTINEL}\n\n"
