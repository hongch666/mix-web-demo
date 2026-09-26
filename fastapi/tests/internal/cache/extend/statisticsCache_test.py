from unittest.mock import AsyncMock, Mock

import pytest

from app.core.constants import RedisKeys
from app.internal.cache import baseCache as base_cache
from app.internal.cache.extend import statisticsCache as module
from app.internal.models import AdsPlatformStats


class _FakeRedis:
    """最小 Redis 替身，记录读写调用，不连接真实 Redis"""

    def __init__(self) -> None:
        self.get = AsyncMock(return_value=None)
        self.set = AsyncMock(return_value=True)
        self.delete = AsyncMock(return_value=True)


@pytest.fixture
def cache(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[module.StatisticsCache, _FakeRedis]:
    fake_redis = _FakeRedis()
    monkeypatch.setattr(base_cache, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(base_cache, "Logger", Mock())
    monkeypatch.setattr(module, "Logger", Mock())
    return module.StatisticsCache(), fake_redis


# StatisticsCache 常量指向平台统计数仓表，L1 TTL 为 600 秒
def test_cache_constants_target_platform_stats_warehouse_table(
    cache: tuple[module.StatisticsCache, _FakeRedis],
) -> None:
    instance, _ = cache

    assert instance.REDIS_KEY_PREFIX == RedisKeys.ARTICLE_STATISTICS
    assert instance.REDIS_VERSION_KEY == RedisKeys.ARTICLE_STATISTICS_VERSION
    assert instance.L1_CACHE_TTL == 600
    assert instance.VERSION_MODEL is AdsPlatformStats


# 版本变化时清空各级缓存并返回 None
@pytest.mark.anyio
async def test_get_returns_none_and_clears_when_version_changed(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[module.StatisticsCache, _FakeRedis],
) -> None:
    instance, _ = cache
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=True))
    clear = AsyncMock()
    monkeypatch.setattr(instance, "clear_all", clear)

    assert await instance.get() is None
    clear.assert_awaited_once()


# 版本未变且 L1 命中时直接返回本地缓存数据
@pytest.mark.anyio
async def test_get_returns_local_data_on_l1_hit(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[module.StatisticsCache, _FakeRedis],
) -> None:
    instance, _ = cache
    await instance.update_local_cache({"totalViews": 10})
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=False))

    assert await instance.get() == {"totalViews": 10}


# L1 未命中时按前缀键读 L2 并回填 L1 再返回数据
@pytest.mark.anyio
async def test_get_reads_redis_and_warms_local_on_l1_miss(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[module.StatisticsCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=False))
    fake_redis.get.return_value = {"totalViews": 20}

    assert await instance.get() == {"totalViews": 20}

    fake_redis.get.assert_awaited_once_with(RedisKeys.ARTICLE_STATISTICS)
    assert instance._local_cache == {"totalViews": 20}


# L1 与 L2 均未命中时返回 None
@pytest.mark.anyio
async def test_get_returns_none_when_both_levels_miss(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[module.StatisticsCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=False))
    fake_redis.get.return_value = None

    assert await instance.get() is None


# 写入时同时更新 L1、L2 并提交版本号
@pytest.mark.anyio
async def test_set_writes_both_levels_and_commits_version(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[module.StatisticsCache, _FakeRedis],
) -> None:
    instance, _ = cache
    update_local = AsyncMock()
    update_redis = AsyncMock()
    update_version = AsyncMock()
    monkeypatch.setattr(instance, "update_local_cache", update_local)
    monkeypatch.setattr(instance, "update_redis_cache", update_redis)
    monkeypatch.setattr(instance, "update_version", update_version)

    await instance.set({"totalViews": 10})

    update_local.assert_awaited_once_with({"totalViews": 10})
    update_redis.assert_awaited_once_with({"totalViews": 10})
    update_version.assert_awaited_once()


# 工厂函数返回经 lru_cache 缓存的同一 StatisticsCache 实例
def test_factory_returns_lru_cached_singleton(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_redis = _FakeRedis()
    monkeypatch.setattr(base_cache, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(module, "_statistics_cache_instance", None)
    module.get_statistics_cache.cache_clear()
    try:
        first = module.get_statistics_cache()
        second = module.get_statistics_cache()

        assert isinstance(first, module.StatisticsCache)
        assert first is second
    finally:
        module.get_statistics_cache.cache_clear()
