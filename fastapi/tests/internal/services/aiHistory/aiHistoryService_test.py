from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.constants import HttpCode, Messages
from app.core.errors import BusinessException
from app.internal.models import AiHistory
from app.internal.services.aiHistory.aiHistoryService import (
    AiHistoryService,
    get_ai_history_service,
)


def _make_service_with_summary() -> tuple[
    AiHistoryService, AsyncMock, AsyncMock, AsyncMock
]:
    """构造被测服务并额外返回记忆摘要 Mapper，供删除联动用例断言"""
    mapper = AsyncMock()
    spring_client = AsyncMock()
    summary_mapper = AsyncMock()
    service = AiHistoryService(mapper, spring_client, summary_mapper)
    return service, mapper, spring_client, summary_mapper


def _make_service() -> tuple[AiHistoryService, AsyncMock, AsyncMock]:
    """构造注入了 Fake Mapper 与 Fake SpringClient 的被测服务"""
    service, mapper, spring_client, _summary_mapper = _make_service_with_summary()
    return service, mapper, spring_client


# dict 入参映射为 ORM 字段并透传 db，空 thinking 归一为 None
@pytest.mark.anyio
async def test_create_ai_history_maps_dict_and_clears_empty_thinking() -> None:
    service, mapper, _spring = _make_service()
    mapper.create_ai_history_async.return_value = "persisted"
    db = Mock()

    result = await service.create_ai_history(
        {"user_id": 7, "ask": "问", "reply": "答", "thinking": "", "ai_type": "gpt"},
        db,
    )

    assert result == "persisted"
    history, passed_db = mapper.create_ai_history_async.await_args.args
    assert isinstance(history, AiHistory)
    assert history.user_id == 7
    assert history.ask == "问"
    assert history.reply == "答"
    assert history.ai_type == "gpt"
    assert history.thinking is None
    assert passed_db is db


# thinking 非空时原样保留到落库实例
@pytest.mark.anyio
async def test_create_ai_history_keeps_non_empty_thinking() -> None:
    service, mapper, _spring = _make_service()
    mapper.create_ai_history_async.return_value = "ok"

    await service.create_ai_history(
        {"user_id": 1, "ask": "a", "reply": "r", "thinking": "推理", "ai_type": "gpt"},
        Mock(),
    )

    history = mapper.create_ai_history_async.await_args.args[0]
    assert history.thinking == "推理"


# 传入 ORM 实例时重建新实例并复制字段，不落库原对象
@pytest.mark.anyio
async def test_create_ai_history_rebuilds_orm_instance() -> None:
    service, mapper, _spring = _make_service()
    mapper.create_ai_history_async.return_value = "ok"
    source = AiHistory(user_id=2, ask="a", reply="r", thinking=None, ai_type="glm")

    await service.create_ai_history(source, Mock())

    history = mapper.create_ai_history_async.await_args.args[0]
    assert history is not source
    assert (history.user_id, history.ai_type) == (2, "glm")


# 缺少必填字段时抛 KeyError 且不触发落库
@pytest.mark.anyio
async def test_create_ai_history_raises_when_required_field_missing() -> None:
    service, mapper, _spring = _make_service()

    with pytest.raises(KeyError):
        await service.create_ai_history({"user_id": 1}, Mock())

    mapper.create_ai_history_async.assert_not_awaited()


# 查询结果序列化并格式化时间，同时绑定用户 id 与分页参数
@pytest.mark.anyio
async def test_get_all_ai_history_serializes_rows_and_binds_user() -> None:
    service, mapper, _spring = _make_service()
    mapper.get_all_ai_history_by_userid_async.return_value = [
        AiHistory(
            id=1,
            user_id=7,
            ask="a",
            reply="r",
            thinking=None,
            ai_type="gpt",
            created_at=datetime(2026, 1, 2, 3, 4, 5),
            updated_at=None,
        )
    ]
    db = Mock()

    rows = await service.get_all_ai_history(7, db)

    assert rows == [
        {
            "id": 1,
            "user_id": 7,
            "ask": "a",
            "reply": "r",
            "thinking": None,
            "ai_type": "gpt",
            "created_at": "2026-01-02 03:04:05",
            "updated_at": None,
        }
    ]
    mapper.get_all_ai_history_by_userid_async.assert_awaited_once_with(db, 7, None)


# 用户不存在时抛 404 业务异常且不执行删除
@pytest.mark.anyio
async def test_delete_by_userid_raises_when_user_missing() -> None:
    service, mapper, spring = _make_service()
    spring.get_users_by_ids.return_value = []
    db = Mock()

    with pytest.raises(BusinessException) as error:
        await service.delete_ai_history_by_userid(7, db)

    assert error.value.status_code == HttpCode.NOT_FOUND
    assert error.value.message == Messages.USER_NOT_EXISTS_ERROR
    assert error.value.error == Messages.ERROR_USER_NOT_FOUND
    spring.get_users_by_ids.assert_awaited_once_with([7])
    mapper.delete_ai_history_by_userid_async.assert_not_awaited()


# 用户存在时按 user_id 委托 mapper 删除，并联动清空记忆摘要后统一提交
@pytest.mark.anyio
async def test_delete_by_userid_delegates_when_user_exists() -> None:
    service, mapper, spring, summary_mapper = _make_service_with_summary()
    spring.get_users_by_ids.return_value = [{"id": 7}]
    db = AsyncMock()

    await service.delete_ai_history_by_userid(7, db)

    spring.get_users_by_ids.assert_awaited_once_with([7])
    mapper.delete_ai_history_by_userid_async.assert_awaited_once_with(db, 7)
    summary_mapper.delete_by_user_id_async.assert_awaited_once_with(db, 7)
    db.commit.assert_awaited_once_with()
    db.rollback.assert_not_awaited()


# 摘要删除失败时整体回滚且不提交，避免出现历史已清空但记忆仍在
@pytest.mark.anyio
async def test_delete_by_userid_rolls_back_when_summary_delete_fails() -> None:
    service, mapper, spring, summary_mapper = _make_service_with_summary()
    spring.get_users_by_ids.return_value = [{"id": 7}]
    summary_mapper.delete_by_user_id_async.side_effect = RuntimeError("db down")
    db = AsyncMock()

    with pytest.raises(RuntimeError):
        await service.delete_ai_history_by_userid(7, db)

    mapper.delete_ai_history_by_userid_async.assert_awaited_once_with(db, 7)
    db.commit.assert_not_awaited()
    db.rollback.assert_awaited_once_with()


# 归一化兼容旧式 dict 方法的对象
def test_normalize_supports_legacy_dict_method() -> None:
    class _LegacyPayload:
        def dict(self) -> dict[str, object]:
            return {
                "user_id": 4,
                "ask": "a",
                "reply": "r",
                "thinking": "t",
                "ai_type": "glm",
            }

    normalized = AiHistoryService._normalize_ai_history_data(_LegacyPayload())

    assert normalized["user_id"] == 4
    assert normalized["ai_type"] == "glm"


# created_at 与 updated_at 缺失时序列化为 None
def test_serialize_returns_none_for_absent_timestamps() -> None:
    history = AiHistory(
        id=8, user_id=1, ask="a", reply="r", thinking=None, ai_type="gpt"
    )

    payload = AiHistoryService._serialize_ai_history(history)

    assert payload["created_at"] is None
    assert payload["updated_at"] is None


# 工厂函数对相同依赖返回同一缓存单例
def test_factory_returns_cached_singleton() -> None:
    mapper = AsyncMock()
    spring_client = AsyncMock()

    assert get_ai_history_service(mapper, spring_client) is get_ai_history_service(
        mapper, spring_client
    )
