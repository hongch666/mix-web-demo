"""聊天请求格式参数的单元测试"""

import pytest
from pydantic import ValidationError

from app.internal.schemas import (
    AIServiceType,
    ChatRequest,
    ChatStreamRequest,
    StreamFormat,
)


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


# 空白消息被 message 校验器拒绝
def test_chat_request_rejects_blank_message() -> None:
    with pytest.raises(ValidationError) as error:
        ChatRequest(message="   ")

    assert error.value.errors()[0]["type"] == "message_empty"


# 白名单外的 service 值被校验拒绝
def test_chat_request_rejects_unknown_service() -> None:
    with pytest.raises(ValidationError) as error:
        ChatRequest(message="你好", service="Unknown")

    assert error.value.errors()[0]["type"] == "service_invalid"


# 白名单内的合法 service 值正常放行
def test_chat_request_accepts_whitelisted_service() -> None:
    request = ChatRequest(message="你好", service="Qwen")

    assert request.service == AIServiceType.QWEN
