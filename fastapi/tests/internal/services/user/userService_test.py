from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from dateutil.relativedelta import relativedelta

from app.internal.services.user import userService as service_module
from app.internal.services.user.userService import UserService, get_user_service


@pytest.fixture
def service_deps(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[UserService, AsyncMock, AsyncMock, AsyncMock]:
    monkeypatch.setattr(service_module, "Logger", Mock())
    spring_client = AsyncMock()
    nestjs_client = AsyncMock()
    user_mapper = AsyncMock()
    service = UserService(spring_client, nestjs_client, user_mapper)
    return service, spring_client, nestjs_client, user_mapper


# day 周期返回 7 天窗口且起点对齐到当日零点
def test_period_dates_day_window() -> None:
    start, end, count, label = UserService._period_dates("day")

    assert (count, label) == (7, "date")
    assert start == start.replace(hour=0, minute=0, second=0, microsecond=0)
    assert end > start


# month 周期返回 6 个月窗口且起点对齐到月初
def test_period_dates_month_window() -> None:
    start, end, count, label = UserService._period_dates("month")

    assert (count, label) == (6, "month")
    assert (start.day, start.hour, start.minute) == (1, 0, 0)
    assert end > start


# year 周期返回 3 年窗口且起点对齐到年初
def test_period_dates_year_window() -> None:
    start, end, count, label = UserService._period_dates("year")

    assert (count, label) == (3, "year")
    assert (start.month, start.day) == (1, 1)
    assert end > start


# day 时间线按天倒序生成并把缺失日期计数补为 0
def test_build_period_timeline_day_fills_missing_dates() -> None:
    timeline = UserService._build_period_timeline(
        "day", datetime(2026, 9, 20), 3, [{"date": "2026-09-21", "count": 4}]
    )

    assert timeline == [
        {"date": "2026-09-22", "count": 0},
        {"date": "2026-09-21", "count": 4},
        {"date": "2026-09-20", "count": 0},
    ]


# month 时间线使用 month 键并按月倒序补齐
def test_build_period_timeline_month_uses_month_key() -> None:
    timeline = UserService._build_period_timeline(
        "month", datetime(2026, 7, 1), 3, [{"date": "2026-08", "count": 2}]
    )

    assert timeline == [
        {"month": "2026-09", "count": 0},
        {"month": "2026-08", "count": 2},
        {"month": "2026-07", "count": 0},
    ]


# year 时间线使用 year 键并按年倒序补齐
def test_build_period_timeline_year_uses_year_key() -> None:
    timeline = UserService._build_period_timeline(
        "year", datetime(2024, 1, 1), 3, [{"date": "2025", "count": 9}]
    )

    assert timeline == [
        {"year": "2026", "count": 0},
        {"year": "2025", "count": 9},
        {"year": "2024", "count": 0},
    ]


# day 周期优先读 ClickHouse 并按日期填充计数
@pytest.mark.anyio
async def test_new_followers_day_reads_clickhouse_rows(service_deps) -> None:
    service, spring, _nestjs, mapper = service_deps
    start, _end, _count, _label = UserService._period_dates("day")
    target = start + timedelta(days=3)
    mapper.get_new_followers_by_day.return_value = [{"date": target.date(), "count": 5}]

    result = await service.get_new_followers_service(11, "day")

    assert result["period"] == "day"
    assert len(result["timeline"]) == 7
    entry = next(
        item
        for item in result["timeline"]
        if item["date"] == target.strftime("%Y-%m-%d")
    )
    assert entry["count"] == 5
    assert mapper.get_new_followers_by_day.await_args.args[0] == 11
    spring.get_followers_in_period.assert_not_awaited()


# month 周期把按天数据聚合到月且同月计数累加
@pytest.mark.anyio
async def test_new_followers_month_groups_rows_by_month(service_deps) -> None:
    service, _spring, _nestjs, mapper = service_deps
    start, _end, _count, _label = UserService._period_dates("month")
    second = start + relativedelta(months=1)
    mapper.get_new_followers_by_day.return_value = [
        {"date": start.date(), "count": 2},
        {"date": start.date(), "count": 3},
        {"date": second.date(), "count": 4},
    ]

    result = await service.get_new_followers_service(9, "month")

    assert result["period"] == "month"
    assert len(result["timeline"]) == 6
    by_month = {item["month"]: item["count"] for item in result["timeline"]}
    assert by_month[start.strftime("%Y-%m")] == 5
    assert by_month[second.strftime("%Y-%m")] == 4


# ClickHouse 失败时 day 周期按 7 个远端窗口降级
@pytest.mark.anyio
async def test_new_followers_day_degrades_to_remote_windows(service_deps) -> None:
    service, spring, _nestjs, mapper = service_deps
    mapper.get_new_followers_by_day.side_effect = RuntimeError("clickhouse down")
    spring.get_followers_in_period.return_value = 2

    result = await service.get_new_followers_service(3, "day")

    assert result["period"] == "day"
    assert len(result["timeline"]) == 7
    assert all(item["count"] == 2 for item in result["timeline"])
    assert spring.get_followers_in_period.await_count == 7
    first_call = spring.get_followers_in_period.await_args_list[0].args
    assert first_call[0] == 3
    assert isinstance(first_call[1], str)
    assert isinstance(first_call[2], str)


# ClickHouse 失败时 month 周期按 6 个远端窗口降级
@pytest.mark.anyio
async def test_new_followers_month_degrades_to_remote_windows(service_deps) -> None:
    service, spring, _nestjs, mapper = service_deps
    mapper.get_new_followers_by_day.side_effect = RuntimeError("clickhouse down")
    spring.get_followers_in_period.return_value = 1

    result = await service.get_new_followers_service(3, "month")

    assert result["period"] == "month"
    assert len(result["timeline"]) == 6
    assert spring.get_followers_in_period.await_count == 6


# ClickHouse 失败时 year 周期按 3 个远端窗口降级
@pytest.mark.anyio
async def test_new_followers_year_degrades_to_remote_windows(service_deps) -> None:
    service, spring, _nestjs, mapper = service_deps
    mapper.get_new_followers_by_day.side_effect = RuntimeError("clickhouse down")
    spring.get_followers_in_period.return_value = 0

    result = await service.get_new_followers_service(3, "year")

    assert result["period"] == "year"
    assert len(result["timeline"]) == 3
    assert spring.get_followers_in_period.await_count == 3


# ClickHouse 与远端窗口全部失败时返回空时间线
@pytest.mark.anyio
async def test_new_followers_returns_empty_timeline_when_all_sources_fail(
    service_deps,
) -> None:
    service, spring, _nestjs, mapper = service_deps
    mapper.get_new_followers_by_day.side_effect = RuntimeError("clickhouse down")
    spring.get_followers_in_period.side_effect = RuntimeError("spring down")

    result = await service.get_new_followers_service(3, "day")

    assert result == {"period": "day", "timeline": []}


# ClickHouse 有数据时直接采用且不调用 NestJS
@pytest.mark.anyio
async def test_article_view_distribution_prefers_clickhouse(service_deps) -> None:
    service, _spring, nestjs, mapper = service_deps
    rows = {"total_views": 10, "articles": [{"article_id": 1, "views": 10}]}
    mapper.get_article_view_distribution.return_value = rows

    assert await service.get_article_view_distribution_service(7) is rows
    nestjs.get_article_view_distribution.assert_not_awaited()


# ClickHouse 失败时降级调用 NestJS 阅读分布
@pytest.mark.anyio
async def test_article_view_distribution_degrades_to_remote(service_deps) -> None:
    service, _spring, nestjs, mapper = service_deps
    mapper.get_article_view_distribution.side_effect = RuntimeError("clickhouse down")
    nestjs.get_article_view_distribution.return_value = {
        "total_views": 1,
        "articles": [],
    }

    result = await service.get_article_view_distribution_service(7)

    assert result == {"total_views": 1, "articles": []}
    nestjs.get_article_view_distribution.assert_awaited_once_with(7)


# 两路数据源均失败时返回零值阅读分布
@pytest.mark.anyio
async def test_article_view_distribution_returns_zero_when_all_fail(
    service_deps,
) -> None:
    service, _spring, nestjs, mapper = service_deps
    mapper.get_article_view_distribution.side_effect = RuntimeError("clickhouse down")
    nestjs.get_article_view_distribution.side_effect = RuntimeError("remote down")

    assert await service.get_article_view_distribution_service(7) == {
        "total_views": 0,
        "articles": [],
    }


# ClickHouse 有数据时直接采用且不调远端关注统计
@pytest.mark.anyio
async def test_author_follow_statistics_prefers_clickhouse(service_deps) -> None:
    service, spring, _nestjs, mapper = service_deps
    rows = {"total_authors": 3, "daily_follows": [{"date": "2026-09-01", "count": 1}]}
    mapper.get_author_follow_statistics.return_value = rows

    assert await service.get_author_follow_statistics_service(7) is rows
    spring.get_total_follows.assert_not_awaited()


# ClickHouse 失败时降级为远端总数与逐日关注窗口
@pytest.mark.anyio
async def test_author_follow_statistics_degrades_to_remote(service_deps) -> None:
    service, spring, _nestjs, mapper = service_deps
    mapper.get_author_follow_statistics.side_effect = RuntimeError("clickhouse down")
    spring.get_total_follows.return_value = 8
    spring.get_daily_follows.return_value = {"daily_follows": [{"count": 4}]}

    result = await service.get_author_follow_statistics_service(7)

    assert result["total_authors"] == 8
    assert len(result["daily_follows"]) == 7
    assert all(item["count"] == 4 for item in result["daily_follows"])
    assert spring.get_daily_follows.await_count == 7


# ClickHouse 与远端均失败时返回空关注统计
@pytest.mark.anyio
async def test_author_follow_statistics_returns_empty_when_all_fail(
    service_deps,
) -> None:
    service, spring, _nestjs, mapper = service_deps

    # 用真实协程替代 AsyncMock.side_effect：mock 协程被 gather 提前取消时会留下未 await 的协程告警
    async def failing_clickhouse(
        *_args: object, **_kwargs: object
    ) -> dict[str, object]:
        raise RuntimeError("clickhouse down")

    async def failing_total_follows(*_args: object, **_kwargs: object) -> int:
        raise RuntimeError("remote down")

    async def empty_daily_follows(
        *_args: object, **_kwargs: object
    ) -> dict[str, object]:
        return {"daily_follows": []}

    mapper.get_author_follow_statistics = failing_clickhouse
    spring.get_total_follows = failing_total_follows
    spring.get_daily_follows = empty_daily_follows

    assert await service.get_author_follow_statistics_service(7) == {
        "total_authors": 0,
        "daily_follows": [],
    }


_TREND_CASES = [
    ("get_monthly_comment_trend_service", "comment_count", "get_monthly_comment_trend"),
    ("get_monthly_like_trend_service", "like_count", "get_monthly_like_trend"),
    ("get_monthly_collect_trend_service", "collect_count", "get_monthly_collect_trend"),
]


# 月度趋势按方法读取对应指标并透传月初时间与 metric
@pytest.mark.anyio
@pytest.mark.parametrize(("method_name", "metric", "spring_method"), _TREND_CASES)
async def test_monthly_trend_reads_configured_metric(
    service_deps, method_name: str, metric: str, spring_method: str
) -> None:
    service, spring, _nestjs, mapper = service_deps
    rows = {"total": 3, "daily_trends": [{"date": "2026-09-01", "count": 3}]}
    mapper.get_monthly_action_trend.return_value = rows

    result = await getattr(service, method_name)(7)

    assert result is rows
    args = mapper.get_monthly_action_trend.await_args.args
    assert args[0] == 7
    assert args[1] == metric
    assert args[2].day == 1
    assert getattr(spring, spring_method).await_count == 0


# ClickHouse 失败时月度趋势降级为远端指标结果
@pytest.mark.anyio
@pytest.mark.parametrize(("method_name", "metric", "spring_method"), _TREND_CASES)
async def test_monthly_trend_degrades_to_remote(
    service_deps, method_name: str, metric: str, spring_method: str
) -> None:
    service, spring, _nestjs, mapper = service_deps
    mapper.get_monthly_action_trend.side_effect = RuntimeError("clickhouse down")
    remote = {"total": 9, "daily_trends": []}
    getattr(spring, spring_method).return_value = remote

    assert await getattr(service, method_name)(7) is remote


# ClickHouse 与远端均失败时月度趋势返回空结构
@pytest.mark.anyio
@pytest.mark.parametrize(("method_name", "metric", "spring_method"), _TREND_CASES)
async def test_monthly_trend_returns_empty_when_all_fail(
    service_deps, method_name: str, metric: str, spring_method: str
) -> None:
    service, spring, _nestjs, mapper = service_deps
    mapper.get_monthly_action_trend.side_effect = RuntimeError("clickhouse down")
    getattr(spring, spring_method).side_effect = RuntimeError("remote down")

    assert await getattr(service, method_name)(7) == {
        "total": 0,
        "daily_trends": [],
    }


# ClickHouse 有画像时直接采用且不调远端统计
@pytest.mark.anyio
async def test_user_profile_prefers_clickhouse(service_deps) -> None:
    service, spring, _nestjs, mapper = service_deps
    profile = {"user_id": 7, "total_articles": 2}
    mapper.get_user_profile.return_value = profile

    assert await service.get_user_profile_service(7) is profile
    spring.get_user_article_count.assert_not_awaited()


# ClickHouse 失败时并行调用多个远端统计并归一空值
@pytest.mark.anyio
async def test_user_profile_degrades_to_parallel_remote_calls(service_deps) -> None:
    service, spring, _nestjs, mapper = service_deps
    mapper.get_user_profile.side_effect = RuntimeError("clickhouse down")
    spring.get_user_article_count.return_value = 4
    spring.get_user_total_views.return_value = "12"
    spring.get_user_total_likes.return_value = None
    spring.get_user_total_collects.return_value = 6
    spring.get_user_total_followers.return_value = 8

    result = await service.get_user_profile_service(7)

    assert result == {
        "user_id": 7,
        "user_name": "",
        "total_articles": 4,
        "total_views_received": 12,
        "total_likes_received": 0,
        "total_collects_received": 6,
        "total_followers": 8,
        "total_likes_given": 0,
        "total_collects_given": 0,
        "total_comments": 0,
        "total_focus": 0,
        "last_active_time": None,
    }
    spring.get_user_article_count.assert_awaited_once_with(7)
    spring.get_user_total_followers.assert_awaited_once_with(7)


# 远端统计失败时用户画像向上抛出异常
@pytest.mark.anyio
async def test_user_profile_remote_failure_propagates(service_deps) -> None:
    service, spring, _nestjs, mapper = service_deps
    mapper.get_user_profile.side_effect = RuntimeError("clickhouse down")
    spring.get_user_article_count.return_value = 1
    spring.get_user_total_views.side_effect = RuntimeError("spring down")
    spring.get_user_total_likes.return_value = 0
    spring.get_user_total_collects.return_value = 0
    spring.get_user_total_followers.return_value = 0

    with pytest.raises(RuntimeError, match="spring down"):
        await service.get_user_profile_service(7)


# 工厂函数对相同依赖返回同一缓存单例
def test_factory_returns_cached_singleton() -> None:
    spring_client = AsyncMock()
    nestjs_client = AsyncMock()
    user_mapper = AsyncMock()

    assert get_user_service(
        spring_client, nestjs_client, user_mapper
    ) is get_user_service(spring_client, nestjs_client, user_mapper)
