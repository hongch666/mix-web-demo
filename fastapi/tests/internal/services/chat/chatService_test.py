"""聊天历史写入的业务规则测试"""

from unittest.mock import AsyncMock

import pytest

from app.internal.schemas import AIServiceType
from app.internal.services.chat.chatService import (
    persist_chat_history,
    select_chat_model,
)


@pytest.mark.parametrize("service", list(AIServiceType))
def test_select_chat_model_uses_requested_provider(service: AIServiceType) -> None:
    models = {provider: object() for provider in AIServiceType}

    assert select_chat_model(service, models) is models[service]


@pytest.mark.anyio
async def test_persist_chat_history_saves_real_user_and_compact_note() -> None:
    history_service = AsyncMock()
    db = object()

    saved = await persist_chat_history(
        history_service,
        db,
        "7",
        "问题",
        "回答",
        "压缩摘要",
        AIServiceType.GPT,
    )

    assert saved is True
    history, passed_db = history_service.create_ai_history.await_args.args
    assert passed_db is db
    assert history.user_id == 7
    assert history.ask == "问题"
    assert history.reply == "回答"
    assert history.thinking == "压缩摘要"
    assert history.ai_type == AIServiceType.GPT.value


@pytest.mark.anyio
@pytest.mark.parametrize("user_id", ["-1", "0", "", "invalid"])
async def test_persist_chat_history_skips_system_identity(user_id: str) -> None:
    history_service = AsyncMock()

    saved = await persist_chat_history(
        history_service,
        object(),
        user_id,
        "问题",
        "回答",
        None,
        AIServiceType.GLM,
    )

    assert saved is False
    history_service.create_ai_history.assert_not_awaited()


@pytest.mark.anyio
async def test_persist_chat_history_normalizes_empty_thinking() -> None:
    history_service = AsyncMock()

    await persist_chat_history(
        history_service, object(), "7", "问题", "回答", "", AIServiceType.QWEN
    )

    history = history_service.create_ai_history.await_args.args[0]
    assert history.thinking is None


@pytest.mark.anyio
async def test_persist_chat_history_propagates_write_failure() -> None:
    history_service = AsyncMock()
    history_service.create_ai_history.side_effect = RuntimeError("write failed")

    with pytest.raises(RuntimeError, match="write failed"):
        await persist_chat_history(
            history_service,
            object(),
            "7",
            "问题",
            "回答",
            None,
            AIServiceType.GPT,
        )
