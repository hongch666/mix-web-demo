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


class _FakeDeleteSession(_FakeSession):
    """覆盖删除路径的会话边界，记录删除、flush 与 commit 次数"""

    def __init__(self, rows: list[Any]) -> None:
        super().__init__(rows)
        self.deleted: list[Any] = []
        self.flushes = 0
        self.commits = 0

    async def delete(self, row: Any) -> None:
        self.deleted.append(row)

    async def flush(self) -> None:
        self.flushes += 1

    async def commit(self) -> None:
        self.commits += 1


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


# 取水位线之后最早的一批记录时按 id 正序读取并限制条数
@pytest.mark.anyio
async def test_oldest_history_after_watermark_uses_ascending_order() -> None:
    mapper = AiHistoryMapper()
    session = _FakeSession([_FakeHistory(3), _FakeHistory(4)])

    result = await mapper.get_oldest_ai_history_after_id_async(session, 7, 2, 2)

    assert [row.id for row in result] == [3, 4]
    sql = str(session.statements[0])
    assert "ASC" in sql
    assert "LIMIT" in sql


# 按用户删除只落到会话并 flush，事务由调用方提交以保证与摘要删除原子
@pytest.mark.anyio
async def test_delete_by_userid_defers_commit_to_caller() -> None:
    mapper = AiHistoryMapper()
    session = _FakeDeleteSession([_FakeHistory(1), _FakeHistory(2)])

    await mapper.delete_ai_history_by_userid_async(session, 7)

    assert [row.id for row in session.deleted] == [1, 2]
    assert session.flushes == 1
    assert session.commits == 0
