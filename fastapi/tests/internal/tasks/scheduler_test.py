from datetime import datetime
from typing import Any
from unittest.mock import Mock

import pytest

from app.internal.tasks import scheduler as scheduler_module


class FakeScheduler:
    """记录 add_job 调用的假调度器，避免真实启动 APScheduler"""

    def __init__(self, **kwargs: Any) -> None:
        self.init_kwargs: dict[str, Any] = kwargs
        self.jobs: list[dict[str, Any]] = []
        self.started = False

    def add_job(self, func: Any, trigger: Any, **kwargs: Any) -> None:
        self.jobs.append({"func": func, "trigger": trigger, **kwargs})

    def start(self) -> None:
        self.started = True


def _start_scheduler(
    monkeypatch: pytest.MonkeyPatch, **injected: Any
) -> tuple[Any, FakeScheduler]:
    created: list[FakeScheduler] = []

    def factory(**kwargs: Any) -> FakeScheduler:
        fake = FakeScheduler(**kwargs)
        created.append(fake)
        return fake

    monkeypatch.setattr(scheduler_module, "Logger", Mock())
    monkeypatch.setattr(scheduler_module, "AsyncIOScheduler", factory)

    result = scheduler_module.start_scheduler(**injected)
    return result, created[0]


def _jobs_by_id(fake: FakeScheduler) -> dict[str, dict[str, Any]]:
    return {job["id"]: job for job in fake.jobs}


# 启动调度器后注册全部 5 个定时任务并应用 coalesce 与单实例默认配置
def test_registers_all_expected_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    result, fake = _start_scheduler(monkeypatch)

    assert result is fake
    assert fake.started is True
    assert fake.init_kwargs == {"job_defaults": {"coalesce": True, "max_instances": 1}}
    assert set(_jobs_by_id(fake)) == {
        "sync_vectors",
        "update_analyze_caches",
        "sync_neo4j",
        "sync_neo4j_full",
        "sync_clickhouse_warehouse",
    }
    assert all(job["trigger"] == "interval" for job in fake.jobs)


# 向量与图谱每 24 小时、图谱全量每 7 天、缓存与数仓每 10 分钟执行
def test_schedules_expected_intervals(monkeypatch: pytest.MonkeyPatch) -> None:
    _, fake = _start_scheduler(monkeypatch)
    jobs = _jobs_by_id(fake)

    assert jobs["sync_vectors"]["hours"] == 24
    assert jobs["update_analyze_caches"]["minutes"] == 10
    assert jobs["sync_neo4j"]["hours"] == 24
    assert jobs["sync_neo4j_full"]["days"] == 7
    assert jobs["sync_clickhouse_warehouse"]["minutes"] == 10


# 分析缓存任务设置 next_run_time 使其注册后立即执行
def test_analyze_cache_job_runs_immediately(monkeypatch: pytest.MonkeyPatch) -> None:
    _, fake = _start_scheduler(monkeypatch)

    next_run_time = _jobs_by_id(fake)["update_analyze_caches"]["next_run_time"]

    assert isinstance(next_run_time, datetime)


# 数仓任务延迟至多 61 秒启动以等待 Nacos 注册完成
def test_warehouse_job_is_delayed_for_nacos_registration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, fake = _start_scheduler(monkeypatch)

    start_date = _jobs_by_id(fake)["sync_clickhouse_warehouse"]["start_date"]
    delay_seconds = (start_date - datetime.now()).total_seconds()

    assert 0 < delay_seconds <= 61


# 各任务函数注入对应依赖，向量同步开增量且图谱同步区分全量标记
def test_injects_dependencies_into_job_functions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spring_client = Mock()
    nestjs_client = Mock()
    analyze_service = Mock()
    article_mapper = Mock()
    _, fake = _start_scheduler(
        monkeypatch,
        article_mapper=article_mapper,
        analyze_service=analyze_service,
        spring_client=spring_client,
        nestjs_client=nestjs_client,
    )
    jobs = _jobs_by_id(fake)

    vector_keywords = jobs["sync_vectors"]["func"].keywords
    assert vector_keywords["article_mapper"] is article_mapper
    assert vector_keywords["enable_incremental_sync"] is True
    assert (
        jobs["update_analyze_caches"]["func"].keywords["analyze_service"]
        is analyze_service
    )
    assert jobs["sync_neo4j"]["func"].keywords == {"force_full": False}
    assert jobs["sync_neo4j_full"]["func"].keywords == {"force_full": True}
    warehouse_keywords = jobs["sync_clickhouse_warehouse"]["func"].keywords
    assert warehouse_keywords["spring_client"] is spring_client
    assert warehouse_keywords["nestjs_client"] is nestjs_client
