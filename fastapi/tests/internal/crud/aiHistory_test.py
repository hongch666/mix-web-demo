from typing import Any

import pytest

from app.internal.crud import AiHistoryMapper


class _FakeHistory:
    """最小历史记录替身，只需要 id 与问答字段"""

    def __init__(self, history_id: int, ask: str = "问", reply: str = "答") -> None:
        self.id = history_id
        self.ask = ask
        self.reply = reply


class _FakeScalars:
    """替代 SQLAlchemy 结果集的 scalars() 视图"""

    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


class _FakeResult:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def scalars(self) -> _FakeScalars:
        return _FakeScalars(self._rows)


class _FakeSession:
    """只替代会话边界，不建立真实 MySQL 连接"""

    def __init__(self, rows: list[Any]) -> None:
        self.rows = rows
        self.statements: list[Any] = []

    async def execute(self, statement: Any) -> _FakeResult:
        self.statements.append(statement)
        return _FakeResult(self.rows)


# 指定 limit 时按时间倒序取最近记录，再反转为正序供上下文按旧到新拼接
@pytest.mark.anyio
async def test_recent_history_is_reversed_to_chronological_order() -> None:
    mapper = AiHistoryMapper()
    # 数据库按倒序返回最近记录，调用方应拿到正序结果
    session = _FakeSession([_FakeHistory(3), _FakeHistory(2), _FakeHistory(1)])

    result = await mapper.get_all_ai_history_by_userid_async(session, 7, 3)

    assert [row.id for row in result] == [1, 2, 3]
    assert "DESC" in str(session.statements[0])


# 不指定 limit 时按时间正序返回全部记录，不做倒序查询
@pytest.mark.anyio
async def test_full_history_query_keeps_ascending_order() -> None:
    mapper = AiHistoryMapper()
    session = _FakeSession([_FakeHistory(1), _FakeHistory(2)])

    result = await mapper.get_all_ai_history_by_userid_async(session, 7, None)

    assert [row.id for row in result] == [1, 2]
    assert "DESC" not in str(session.statements[0])


# 按压缩水位线读取未压缩历史时使用 id 过滤并反转为正序
@pytest.mark.anyio
async def test_history_after_watermark_is_reversed_to_chronological_order() -> None:
    mapper = AiHistoryMapper()
    # 数据库按 id 倒序返回水位线之后的最近记录
    session = _FakeSession([_FakeHistory(5), _FakeHistory(4), _FakeHistory(3)])

    result = await mapper.get_ai_history_after_id_async(session, 7, 2, 3)

    assert [row.id for row in result] == [3, 4, 5]
    sql = str(session.statements[0])
    assert "DESC" in sql
    assert "LIMIT" in sql
