import importlib
import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, nullcontext
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.base import StreamFrameContext
from app.core.constants import Defaults
from app.internal.schemas import (
    AIServiceType,
    ChatRequest,
    ChatStreamRequest,
    StreamFormat,
)
from app.internal.services.chat import ChatApplicationService, ChatStreamEvent

chat_module = importlib.import_module(
    "app.internal.services.chat.chatApplicationService"
)


def _service(monkeypatch: pytest.MonkeyPatch, user_id: int | None = 7):
    monkeypatch.setattr(chat_module, "get_current_user_id", lambda: user_id)
    monkeypatch.setattr(
        chat_module,
        "load_config",
        lambda name: (
            {"mode": "test"}
            if name == "server"
            else {
                "closeai": {
                    f"{provider}_model_name": "unit-model"
                    for provider in (
                        "gpt",
                        "gemini",
                        "glm",
                        "deepseek",
                        "claude",
                        "qwen",
                    )
                }
            }
        ),
    )
    monkeypatch.setattr(chat_module, "get_langsmith_context", lambda **_: nullcontext())
    model = Mock()
    model.simple_chat = AsyncMock(return_value="回答中有错误二字")
    history = AsyncMock()
    return ChatApplicationService({AIServiceType.GPT: model}, history), model, history


@pytest.mark.anyio
async def test_send_keeps_ordinary_reply_with_error_word_and_saves_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, model, history = _service(monkeypatch)
    db = Mock()

    response = await service.send(
        ChatRequest(message="问题", service=AIServiceType.GPT, conversationId="c-1"), db
    )

    assert response.message == "回答中有错误二字"
    assert response.conversationId == "c-1"
    assert response.userId == "7"
    assert model.simple_chat.await_args.kwargs["raise_on_error"] is True
    saved, passed_db = history.create_ai_history.await_args.args
    assert passed_db is db
    assert saved.user_id == 7
    assert saved.reply == response.message


@pytest.mark.anyio
async def test_send_skips_history_for_system_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, _, history = _service(monkeypatch, None)

    response = await service.send(ChatRequest(message="问题"), Mock())

    assert response.userId == str(Defaults.SYSTEM_USER_ID)
    history.create_ai_history.assert_not_awaited()


@pytest.mark.anyio
async def test_send_propagates_model_failure_without_writing_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, model, history = _service(monkeypatch)
    model.simple_chat.side_effect = RuntimeError("模型失败")

    with pytest.raises(RuntimeError, match="模型失败"):
        await service.send(ChatRequest(message="问题"), Mock())

    history.create_ai_history.assert_not_awaited()


@pytest.mark.anyio
async def test_stream_saves_content_and_thinking_then_releases_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, model, history = _service(monkeypatch)
    closed = False
    db = Mock()

    async def get_db() -> AsyncGenerator[Mock, None]:
        nonlocal closed
        try:
            yield db
        finally:
            closed = True

    @asynccontextmanager
    async def trace(**_):
        yield

    async def stream_chat(**_):
        yield {"type": Defaults.STREAM_TYPE_THINKING, "content": "推理"}
        yield {"type": Defaults.STREAM_TYPE_CONTENT, "content": "回答"}

    monkeypatch.setattr(chat_module, "get_db", get_db)
    monkeypatch.setattr(chat_module, "get_langsmith_context_async", trace)
    model.stream_chat = stream_chat

    context, events = service.stream(ChatStreamRequest(message="问题"))
    chunks = [event async for event in events]

    assert context.user_id == "7"
    assert [(event.kind, event.content) for event in chunks] == [
        (Defaults.STREAM_TYPE_THINKING, "推理"),
        (Defaults.STREAM_TYPE_CONTENT, "回答"),
    ]
    saved, passed_db = history.create_ai_history.await_args.args
    assert passed_db is db
    assert saved.thinking == "推理"
    assert saved.reply == "回答"
    assert closed is True


def _context() -> StreamFrameContext:
    return StreamFrameContext(
        conversation_id="conversation-1",
        chat_id="chat-1",
        user_id="7",
        service="GPT",
        model="unit-model",
        completion_id="chatcmpl-unit",
        created=1730000000,
    )


def _payload(frame: str) -> dict:
    return json.loads(frame.removeprefix("data: ").strip())


async def _events(*items: ChatStreamEvent) -> AsyncGenerator[ChatStreamEvent, None]:
    for item in items:
        yield item


@pytest.mark.anyio
async def test_stream_frames_uses_request_format_and_service_events() -> None:
    service = ChatApplicationService({}, Mock())
    service.stream = Mock(
        return_value=(
            _context(),
            _events(ChatStreamEvent(Defaults.STREAM_TYPE_CONTENT, "回答")),
        )
    )
    request = ChatStreamRequest(message="问题", streamFormat=StreamFormat.OPENAI)

    frames = [frame async for frame in service.stream_frames(request)]

    service.stream.assert_called_once_with(request)
    assert _payload(frames[1])["choices"][0]["delta"] == {"content": "回答"}


@pytest.mark.anyio
async def test_native_stream_accumulates_content_but_not_thinking() -> None:
    frames = [
        frame
        async for frame in ChatApplicationService.format_stream(
            _context(),
            _events(
                ChatStreamEvent(Defaults.STREAM_TYPE_THINKING, "思考"),
                ChatStreamEvent(Defaults.STREAM_TYPE_CONTENT, "你"),
                ChatStreamEvent(Defaults.STREAM_TYPE_CONTENT, "好"),
            ),
            False,
        )
    ]

    assert [_payload(frame)["data"]["message"] for frame in frames] == [
        "",
        "你",
        "你好",
    ]
    assert [_payload(frame)["data"]["chunk"] for frame in frames] == [
        "思考",
        "你",
        "好",
    ]


@pytest.mark.anyio
async def test_native_stream_emits_done_when_no_content() -> None:
    frames = [
        frame
        async for frame in ChatApplicationService.format_stream(
            _context(),
            _events(ChatStreamEvent(Defaults.STREAM_TYPE_THINKING, "思考")),
            False,
        )
    ]

    assert _payload(frames[-1])["data"]["message_type"] == Defaults.STREAM_TYPE_DONE


@pytest.mark.anyio
async def test_openai_stream_emits_role_error_finish_and_done() -> None:
    frames = [
        frame
        async for frame in ChatApplicationService.format_stream(
            _context(),
            _events(
                ChatStreamEvent(Defaults.STREAM_TYPE_CONTENT, ""),
                ChatStreamEvent(Defaults.STREAM_TYPE_ERROR, "模型异常"),
                ChatStreamEvent(Defaults.STREAM_TYPE_CONTENT, "回答"),
            ),
            True,
        )
    ]

    assert _payload(frames[0])["choices"][0]["delta"] == {"role": "assistant"}
    assert _payload(frames[1]) == {"error": {"message": "模型异常"}}
    assert _payload(frames[2])["choices"][0]["delta"] == {"content": "回答"}
    assert _payload(frames[3])["choices"][0]["finish_reason"] == "stop"
    assert frames[4] == "data: [DONE]\n\n"


@pytest.mark.anyio
async def test_stream_format_closes_source_when_client_disconnects() -> None:
    closed = False

    async def source() -> AsyncGenerator[ChatStreamEvent, None]:
        nonlocal closed
        try:
            yield ChatStreamEvent(Defaults.STREAM_TYPE_CONTENT, "第一段")
            yield ChatStreamEvent(Defaults.STREAM_TYPE_CONTENT, "第二段")
        finally:
            closed = True

    frames = ChatApplicationService.format_stream(_context(), source(), False)
    await anext(frames)
    await frames.aclose()

    assert closed is True
