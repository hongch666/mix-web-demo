from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Any

import pytest

from app.internal.crud import UserMapper
from app.internal.schemas import (
    ActionTrendResponse,
    AuthorFollowStatisticsResponse,
    UserProfileResponse,
)


class _FakeMappings:
    """替代 SQLAlchemy 结果集的 mappings() 视图"""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows: list[dict[str, Any]] = rows

    def all(self) -> list[dict[str, Any]]:
        return self._rows


class _FakeResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows: list[dict[str, Any]] = rows

    def mappings(self) -> _FakeMappings:
        return _FakeMappings(self._rows)


class _FakeSession:
    """只替代会话边界，不建立真实 ClickHouse 连接"""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows: list[dict[str, Any]] = rows

    async def execute(self, statement: Any) -> _FakeResult:
        return _FakeResult(self._rows)


def _build_mapper(rows: list[dict[str, Any]]) -> UserMapper:
    @asynccontextmanager
    async def session_factory() -> AsyncIterator[_FakeSession]:
        yield _FakeSession(rows)

    return UserMapper(session_factory)


def _profile_row(last_active_time: Any) -> dict[str, Any]:
    return {
        "user_id": 7,
        "user_name": "tester",
        "total_articles": 2,
        "total_views_received": 20,
        "total_likes_received": 3,
        "total_collects_received": 1,
        "total_followers": 5,
        "total_likes_given": 4,
        "total_collects_given": 6,
        "total_comments": 7,
        "total_focus": 8,
        "last_active_time": last_active_time,
    }


# ClickHouse DateTime 列的最后活跃时间按字符串返回，响应模型不再校验失败
@pytest.mark.anyio
async def test_user_profile_formats_last_active_time_as_text() -> None:
    mapper = _build_mapper(
        [_profile_row(datetime(2026, 9, 22, 13, 37, 19))],
    )

    result = await mapper.get_user_profile(7)

    profile = UserProfileResponse.model_validate(result)
    assert profile.last_active_time == "2026-09-22 13:37:19"


# 数仓无活跃记录时最后活跃时间保持为空
@pytest.mark.anyio
async def test_user_profile_keeps_empty_last_active_time() -> None:
    mapper = _build_mapper([_profile_row(None)])

    result = await mapper.get_user_profile(7)

    assert UserProfileResponse.model_validate(result).last_active_time is None


# ClickHouse Date 列的每日关注日期按字符串返回，响应模型不再校验失败
@pytest.mark.anyio
async def test_author_follow_statistics_formats_dates_as_text() -> None:
    mapper = _build_mapper(
        [
            {
                "total_followers": 5,
                "date": date(2026, 9, 21),
                "count": 2,
            }
        ]
    )

    result = await mapper.get_author_follow_statistics(
        7, datetime(2026, 9, 21), datetime(2026, 9, 22)
    )

    statistics = AuthorFollowStatisticsResponse.model_validate(result)
    assert statistics.daily_follows[0].date == "2026-09-21"
    assert statistics.daily_follows[0].count == 2


# ClickHouse Date 列的月度趋势日期按字符串返回，响应模型不再校验失败
@pytest.mark.anyio
async def test_monthly_action_trend_formats_dates_as_text() -> None:
    mapper = _build_mapper([{"date": date(2026, 9, 21), "count": 3}])

    result = await mapper.get_monthly_action_trend(
        7, "like_count", datetime(2026, 9, 1), datetime(2026, 10, 1)
    )

    trend = ActionTrendResponse.model_validate(result)
    assert trend.daily_trends[0].date == "2026-09-21"
    assert trend.total == 3
