from unittest.mock import AsyncMock, Mock

import pytest

from app.core.constants import RedisKeys
from app.internal.cache import baseCache as base_cache
from app.internal.cache.extend import articleCache as module
from app.internal.models import AdsTop10Article


class _FakeRedis:
    """最小 Redis 替身，记录读写调用，不连接真实 Redis"""

    def __init__(self) -> None:
        self.get = AsyncMock(return_value=None)
        self.set = AsyncMock(return_value=True)
        self.delete = AsyncMock(return_value=True)


@pytest.fixture
def cache(monkeypatch: pytest.MonkeyPatch) -> tuple[module.ArticleCache, _FakeRedis]:
    fake_redis = _FakeRedis()
    monkeypatch.setattr(base_cache, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(base_cache, "Logger", Mock())
    monkeypatch.setattr(module, "Logger", Mock())
    return module.ArticleCache(), fake_redis


# ArticleCache 常量指向文章 Top10 数仓表，L1 TTL 为 300 秒
def test_cache_constants_target_top10_article_warehouse_table(
    cache: tuple[module.ArticleCache, _FakeRedis],
) -> None:
    instance, _ = cache

    assert instance.REDIS_KEY_PREFIX == RedisKeys.ARTICLE_TOP10
    assert instance.REDIS_VERSION_KEY == RedisKeys.ARTICLE_TOP10_VERSION
    assert instance.L1_CACHE_TTL == 300
    assert instance.VERSION_MODEL is AdsTop10Article


# 版本变化时清空各级缓存并返回 None
@pytest.mark.anyio
async def test_get_returns_none_and_clears_when_version_changed(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[module.ArticleCache, _FakeRedis],
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
    cache: tuple[module.ArticleCache, _FakeRedis],
) -> None:
    instance, _ = cache
    await instance.update_local_cache([{"id": 1}])
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=False))

    assert await instance.get() == [{"id": 1}]


# L1 未命中时按前缀键读 L2 并回填 L1 再返回数据
@pytest.mark.anyio
async def test_get_reads_redis_and_warms_local_on_l1_miss(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[module.ArticleCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=False))
    fake_redis.get.return_value = [{"id": 2}]

    assert await instance.get() == [{"id": 2}]

    fake_redis.get.assert_awaited_once_with(RedisKeys.ARTICLE_TOP10)
    assert instance._local_cache == [{"id": 2}]


# L1 与 L2 均未命中时返回 None
@pytest.mark.anyio
async def test_get_returns_none_when_both_levels_miss(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[module.ArticleCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=False))
    fake_redis.get.return_value = None

    assert await instance.get() is None


# 写入时同时更新 L1、L2 并提交版本号
@pytest.mark.anyio
async def test_set_writes_both_levels_and_commits_version(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[module.ArticleCache, _FakeRedis],
) -> None:
    instance, _ = cache
    update_local = AsyncMock()
    update_redis = AsyncMock()
    update_version = AsyncMock()
    monkeypatch.setattr(instance, "update_local_cache", update_local)
    monkeypatch.setattr(instance, "update_redis_cache", update_redis)
    monkeypatch.setattr(instance, "update_version", update_version)

    await instance.set([{"id": 1}])

    update_local.assert_awaited_once_with([{"id": 1}])
    update_redis.assert_awaited_once_with([{"id": 1}])
    update_version.assert_awaited_once()


# 工厂函数返回经 lru_cache 缓存的同一 ArticleCache 实例
def test_factory_returns_lru_cached_singleton(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_redis = _FakeRedis()
    monkeypatch.setattr(base_cache, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(module, "_article_cache_instance", None)
    module.get_article_cache.cache_clear()
    try:
        first = module.get_article_cache()
        second = module.get_article_cache()

        assert isinstance(first, module.ArticleCache)
        assert first is second
    finally:
        module.get_article_cache.cache_clear()
