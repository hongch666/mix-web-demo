from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.internal.crud import AiUserSummaryMapper


def _make_session(existing: Any) -> AsyncMock:
    """只替代会话边界，摘要查询结果由入参决定"""
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = existing
    session.execute.return_value = result
    return session


# 摘要不存在时删除为空操作，不产生删除与 flush
@pytest.mark.anyio
async def test_delete_by_user_id_is_noop_when_summary_missing() -> None:
    mapper = AiUserSummaryMapper()
    session = _make_session(None)

    await mapper.delete_by_user_id_async(session, 7)

    session.delete.assert_not_awaited()
    session.flush.assert_not_awaited()
    session.commit.assert_not_awaited()


# 摘要存在时只落到会话并 flush，事务由调用方提交以保证与历史删除原子
@pytest.mark.anyio
async def test_delete_by_user_id_defers_commit_to_caller() -> None:
    mapper = AiUserSummaryMapper()
    existing = MagicMock()
    session = _make_session(existing)

    await mapper.delete_by_user_id_async(session, 7)

    session.delete.assert_awaited_once_with(existing)
    session.flush.assert_awaited_once_with()
    session.commit.assert_not_awaited()
