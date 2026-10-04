"""聊天请求格式参数的单元测试"""

import pytest
from pydantic import ValidationError

from app.internal.schemas import ChatStreamRequest, StreamFormat


# streamFormat 是可选参数，不传时保持 native
def test_chat_stream_request_defaults_to_native_format() -> None:
    request = ChatStreamRequest(message="你好")

    assert request.streamFormat is StreamFormat.NATIVE


# 显式传 openai 时切换到标准分片格式
def test_chat_stream_request_accepts_openai_format() -> None:
    request = ChatStreamRequest(message="你好", streamFormat="openai")

    assert request.streamFormat is StreamFormat.OPENAI


# 非法的 streamFormat 被参数校验拒绝
def test_chat_stream_request_rejects_unknown_format() -> None:
    with pytest.raises(ValidationError):
        ChatStreamRequest(message="你好", streamFormat="sse")
