import time
from unittest.mock import AsyncMock, Mock

import pytest

from app.internal.cache import baseCache as base_cache
from app.internal.cache.baseCache import BaseCache


class _FakeRedis:
    """最小 Redis 替身，记录读写调用，不连接真实 Redis"""

    def __init__(self) -> None:
        self.get = AsyncMock(return_value=None)
        self.set = AsyncMock(return_value=True)
        self.delete = AsyncMock(return_value=True)


class _ConcreteCache(BaseCache):
    """用于验证模板类行为的最小实现"""

    REDIS_KEY_PREFIX: str = "test:base:key"
    L1_CACHE_TTL: int = 300

    async def get(self) -> object:
        return await self.get_from_local()

    async def set(self, data: object) -> None:
        await self.update_local_cache(data)


@pytest.fixture
def cache(monkeypatch: pytest.MonkeyPatch) -> tuple[_ConcreteCache, _FakeRedis]:
    fake_redis = _FakeRedis()
    monkeypatch.setattr(base_cache, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(base_cache, "Logger", Mock())
    return _ConcreteCache(), fake_redis


# 初始构造绑定 Redis 客户端，L2 TTL 默认 86400 秒、L1 TTL 取子类 300 秒
def test_init_binds_redis_client_and_default_ttls(
    cache: tuple[_ConcreteCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache

    assert instance._redis is fake_redis
    assert instance._redis_ttl == 86400
    assert instance._local_cache is None
    assert instance._local_cache_time == 0
    assert instance._local_cache_ttl == 300


# 首次写入前 L1 无数据，有效性判定为 False 且读取返回 None
@pytest.mark.anyio
async def test_local_cache_is_invalid_before_first_write(
    cache: tuple[_ConcreteCache, _FakeRedis],
) -> None:
    instance, _ = cache

    assert await instance.is_local_cache_valid() is False
    assert await instance.get_from_local() is None


# 写入空列表后因假值判定为未命中，L1 有效性仍为 False
@pytest.mark.anyio
async def test_falsy_local_cache_is_treated_as_invalid(
    cache: tuple[_ConcreteCache, _FakeRedis],
) -> None:
    instance, _ = cache

    await instance.update_local_cache([])

    # 空列表为假值，判定为未命中，避免把空结果当作有效缓存
    assert await instance.is_local_cache_valid() is False


# 写入数据且在 TTL 内时 L1 判定有效并原样返回缓存内容
@pytest.mark.anyio
async def test_local_cache_hit_returns_data_within_ttl(
    cache: tuple[_ConcreteCache, _FakeRedis],
) -> None:
    instance, _ = cache

    await instance.update_local_cache([{"id": 1}])

    assert await instance.is_local_cache_valid() is True
    assert await instance.get_from_local() == [{"id": 1}]


# 缓存时间回拨到 TTL 之外后 L1 失效且读取返回 None
@pytest.mark.anyio
async def test_local_cache_expires_after_ttl(
    cache: tuple[_ConcreteCache, _FakeRedis],
) -> None:
    instance, _ = cache

    await instance.update_local_cache([{"id": 1}])
    instance._local_cache_time = time.time() - (instance._local_cache_ttl + 1)

    assert await instance.is_local_cache_valid() is False
    assert await instance.get_from_local() is None


# L2 命中时按前缀键读取并回填 L1，返回 Redis 原始字符串
@pytest.mark.anyio
async def test_redis_hit_returns_payload_and_warms_local_cache(
    cache: tuple[_ConcreteCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    fake_redis.get.return_value = '[{"id": 1}]'

    assert await instance.get_from_redis() == '[{"id": 1}]'

    fake_redis.get.assert_awaited_once_with("test:base:key")
    assert instance._local_cache == '[{"id": 1}]'
    assert instance._local_cache_time > 0


# L2 读取返回空值时 get_from_redis 返回 None
@pytest.mark.anyio
async def test_redis_miss_returns_none(
    cache: tuple[_ConcreteCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    fake_redis.get.return_value = None

    assert await instance.get_from_redis() is None


# L2 读取抛异常时降级返回 None 且不污染 L1 状态
@pytest.mark.anyio
async def test_redis_read_failure_degrades_to_none(
    cache: tuple[_ConcreteCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    fake_redis.get.side_effect = RuntimeError("redis down")

    assert await instance.get_from_redis() is None
    assert instance._local_cache is None


# 写 L2 时使用配置键并携带 86400 秒过期时间
@pytest.mark.anyio
async def test_update_redis_cache_sets_value_with_one_day_ttl(
    cache: tuple[_ConcreteCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache

    await instance.update_redis_cache({"id": 1})

    fake_redis.set.assert_awaited_once_with("test:base:key", {"id": 1}, ex=86400)


# L2 写入失败被吞掉且 L1 状态保持为空
@pytest.mark.anyio
async def test_update_redis_cache_failure_does_not_break_local_state(
    cache: tuple[_ConcreteCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    fake_redis.set.side_effect = RuntimeError("redis down")

    await instance.update_redis_cache({"id": 1})

    fake_redis.set.assert_awaited_once()
    assert instance._local_cache is None


# 清空 L1 后缓存数据与时间戳均重置为初始值
@pytest.mark.anyio
async def test_clear_local_cache_resets_state(
    cache: tuple[_ConcreteCache, _FakeRedis],
) -> None:
    instance, _ = cache

    await instance.update_local_cache([{"id": 1}])
    await instance.clear_local_cache()

    assert instance._local_cache is None
    assert instance._local_cache_time == 0


# 清空 L2 时按配置前缀键调用删除
@pytest.mark.anyio
async def test_clear_redis_cache_deletes_configured_key(
    cache: tuple[_ConcreteCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache

    await instance.clear_redis_cache()

    fake_redis.delete.assert_awaited_once_with("test:base:key")


# L2 删除失败被吞掉但仍按配置键发起删除
@pytest.mark.anyio
async def test_clear_redis_cache_failure_is_swallowed(
    cache: tuple[_ConcreteCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    fake_redis.delete.side_effect = RuntimeError("redis down")

    await instance.clear_redis_cache()

    fake_redis.delete.assert_awaited_once_with("test:base:key")


# 整体清空同时重置 L1 并按配置键删除 L2
@pytest.mark.anyio
async def test_clear_all_clears_both_levels(
    cache: tuple[_ConcreteCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache

    await instance.update_local_cache([{"id": 1}])
    await instance.clear_all()

    assert instance._local_cache is None
    fake_redis.delete.assert_awaited_once_with("test:base:key")


# repr 与 str 均返回类名加括号的表示形式
def test_repr_and_str_report_class_name(
    cache: tuple[_ConcreteCache, _FakeRedis],
) -> None:
    instance, _ = cache

    assert repr(instance) == "_ConcreteCache()"
    assert str(instance) == "_ConcreteCache()"
