from collections.abc import Generator
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.constants import RedisKeys
from app.internal.tasks.logic import analyzeCacheTask as task


class FakeRedisClient:
    """最小化模拟 Redis 客户端，只提供分布式锁需要的两个方法"""

    def __init__(self, lock_value: str | None = "lock-value") -> None:
        self.try_lock = AsyncMock(return_value=lock_value)
        self.unlock = AsyncMock(return_value=True)


@pytest.fixture(autouse=True)
def silence_logger(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """分析缓存任务分支众多且都打日志，测试中静默日志避免噪声"""
    monkeypatch.setattr(task, "Logger", Mock())
    yield


def _build_analyze_service() -> Mock:
    service = Mock()
    service.get_top10_articles_service = AsyncMock()
    service.get_wordcloud_service = AsyncMock()
    service.get_article_statistics_service = AsyncMock()
    service.get_category_article_count_service = AsyncMock()
    service.get_monthly_publish_count_service = AsyncMock()
    return service


# 未获取到分布式锁时跳过缓存更新且不释放锁
@pytest.mark.anyio
async def test_skips_update_when_lock_is_not_acquired(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedisClient(None)
    update = AsyncMock()
    monkeypatch.setattr(task, "get_redis_client", lambda: redis_client)
    monkeypatch.setattr(task, "_update_analyze_caches_async", update)

    await task.update_analyze_caches_async(_build_analyze_service())

    update.assert_not_awaited()
    redis_client.unlock.assert_not_awaited()
    redis_client.try_lock.assert_awaited_once_with(
        RedisKeys.LOCK_TASK_ANALYZE_CACHE, RedisKeys.LOCK_TASK_ANALYZE_CACHE_EXPIRE
    )


# 获取锁后执行缓存更新并用持有的锁值释放锁
@pytest.mark.anyio
async def test_releases_lock_with_acquired_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedisClient()
    update = AsyncMock()
    monkeypatch.setattr(task, "get_redis_client", lambda: redis_client)
    monkeypatch.setattr(task, "_update_analyze_caches_async", update)

    await task.update_analyze_caches_async(_build_analyze_service())

    update.assert_awaited_once()
    redis_client.unlock.assert_awaited_once_with(
        RedisKeys.LOCK_TASK_ANALYZE_CACHE, "lock-value"
    )


# 更新抛异常时仍释放锁并向上抛出原始错误
@pytest.mark.anyio
async def test_releases_lock_even_when_update_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis_client = FakeRedisClient()
    monkeypatch.setattr(task, "get_redis_client", lambda: redis_client)
    monkeypatch.setattr(
        task,
        "_update_analyze_caches_async",
        AsyncMock(side_effect=RuntimeError("update failed")),
    )

    with pytest.raises(RuntimeError, match="update failed"):
        await task.update_analyze_caches_async(_build_analyze_service())

    redis_client.unlock.assert_awaited_once_with(
        RedisKeys.LOCK_TASK_ANALYZE_CACHE, "lock-value"
    )


# 传入 None 服务时直接返回且不创建数据库会话
@pytest.mark.anyio
async def test_update_returns_without_service(monkeypatch: pytest.MonkeyPatch) -> None:
    db_factory = Mock()

    await task._update_analyze_caches_async(None, db_factory)

    db_factory.assert_not_called()


# 存在服务时创建会话刷新全部 5 项缓存并关闭会话
@pytest.mark.anyio
async def test_update_refreshes_all_caches_with_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _build_analyze_service()
    db = Mock()
    db.close = AsyncMock()

    await task._update_analyze_caches_async(service, Mock(return_value=db))

    service.get_top10_articles_service.assert_awaited_once_with(db)
    service.get_wordcloud_service.assert_awaited_once_with()
    service.get_article_statistics_service.assert_awaited_once_with(db)
    service.get_category_article_count_service.assert_awaited_once_with(db)
    service.get_monthly_publish_count_service.assert_awaited_once_with(db)
    db.close.assert_awaited_once_with()


# 未提供会话工厂时以 None 会话刷新缓存
@pytest.mark.anyio
async def test_update_passes_none_session_without_db_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _build_analyze_service()

    await task._update_analyze_caches_async(service, None)

    service.get_top10_articles_service.assert_awaited_once_with(None)
    service.get_monthly_publish_count_service.assert_awaited_once_with(None)


# 单项缓存刷新失败不中断，其余缓存仍全部刷新并关闭会话
@pytest.mark.anyio
async def test_update_continues_after_single_cache_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _build_analyze_service()
    service.get_top10_articles_service = AsyncMock(
        side_effect=RuntimeError("top10 failed")
    )
    db = Mock()
    db.close = AsyncMock()

    await task._update_analyze_caches_async(service, Mock(return_value=db))

    service.get_wordcloud_service.assert_awaited_once_with()
    service.get_article_statistics_service.assert_awaited_once_with(db)
    service.get_category_article_count_service.assert_awaited_once_with(db)
    service.get_monthly_publish_count_service.assert_awaited_once_with(db)
    db.close.assert_awaited_once_with()


# 会话关闭抛异常被吞掉不影响任务完成
@pytest.mark.anyio
async def test_update_swallows_session_close_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _build_analyze_service()
    db = Mock()
    db.close = AsyncMock(side_effect=RuntimeError("close failed"))

    await task._update_analyze_caches_async(service, Mock(return_value=db))

    db.close.assert_awaited_once_with()


# 会话工厂创建失败时吞掉异常且不触碰任何缓存
@pytest.mark.anyio
async def test_update_swallows_db_factory_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _build_analyze_service()
    db_factory = Mock(side_effect=RuntimeError("session unavailable"))

    await task._update_analyze_caches_async(service, db_factory)

    service.get_top10_articles_service.assert_not_awaited()
