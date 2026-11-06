import asyncio
import time
from unittest.mock import AsyncMock, Mock

import pytest

from app.internal.cache import KeyedVersionedCache, baseCache as base_cache


class _FakeRedis:
    """最小 Redis 替身，记录读写、删除与按模式批量删除，不连接真实 Redis"""

    def __init__(self) -> None:
        self.get = AsyncMock(return_value=None)
        self.set = AsyncMock(return_value=True)
        self.delete = AsyncMock(return_value=True)
        self.keys = AsyncMock(return_value=[])
        self.delete_by_patterns = AsyncMock(return_value=0)


class _KeyedCache(KeyedVersionedCache):
    """用于验证键分片模板行为的最小实现"""

    REDIS_KEY_PREFIX: str = "test:keyed:"
    REDIS_VERSION_KEY: str = "test:keyed:version"
    L1_CACHE_TTL: int = 60


@pytest.fixture
def cache(monkeypatch: pytest.MonkeyPatch) -> tuple[_KeyedCache, _FakeRedis]:
    fake_redis = _FakeRedis()
    monkeypatch.setattr(base_cache, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(base_cache, "Logger", Mock())
    return _KeyedCache(), fake_redis


# 初始构造只建立空的键分片容器，容量上限与版本号沿用模板默认值
def test_init_starts_with_empty_entries(cache: tuple[_KeyedCache, _FakeRedis]) -> None:
    instance, _ = cache

    assert instance._local_entries == {}
    assert instance._cache_version is None
    assert instance.L1_MAX_ENTRIES == 512


# 键分片缓存不提供无键读取入口
@pytest.mark.anyio
async def test_get_without_key_raises_not_implemented(
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, _ = cache

    with pytest.raises(NotImplementedError):
        await instance.get()


# 键分片缓存不提供无键写入入口
@pytest.mark.anyio
async def test_set_without_key_raises_not_implemented(
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, _ = cache

    with pytest.raises(NotImplementedError):
        await instance.set({"views": 1})


# 版本变化时清空该缓存下的全部键并返回 None，不再读两级缓存
@pytest.mark.anyio
async def test_get_entry_returns_none_and_clears_when_version_changed(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=True))
    clear = AsyncMock()
    monkeypatch.setattr(instance, "clear_all", clear)

    assert await instance.get_entry("u1") is None
    clear.assert_awaited_once()
    fake_redis.get.assert_not_awaited()


# L1 命中且未过期时直接返回本地键值，不访问 Redis
@pytest.mark.anyio
async def test_get_entry_returns_local_value_without_reading_redis(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=False))
    instance._local_entries["u1"] = ([{"views": 3}], time.time())

    assert await instance.get_entry("u1") == [{"views": 3}]
    fake_redis.get.assert_not_awaited()


# L1 未命中时按前缀拼业务键读 L2 并回填本地键值
@pytest.mark.anyio
async def test_get_entry_falls_back_to_prefixed_redis_key_and_warms_local(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=False))
    fake_redis.get.return_value = {"views": 5}

    assert await instance.get_entry("u1") == {"views": 5}

    fake_redis.get.assert_awaited_once_with("test:keyed:u1")
    assert instance._local_entries["u1"][0] == {"views": 5}


# 过期条目在读取时被清理并回退到 Redis
@pytest.mark.anyio
async def test_get_entry_drops_expired_local_entry_and_reloads_from_redis(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=False))
    expired_at = time.time() - instance._local_cache_ttl - 1
    instance._local_entries["u1"] = ({"views": 1}, expired_at)
    fake_redis.get.return_value = {"views": 9}

    assert await instance.get_entry("u1") == {"views": 9}

    fake_redis.get.assert_awaited_once_with("test:keyed:u1")
    assert instance._local_entries["u1"][0] == {"views": 9}


# 两级缓存都没有该业务键时返回 None
@pytest.mark.anyio
async def test_get_entry_returns_none_when_both_levels_miss(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=False))
    fake_redis.get.return_value = None

    assert await instance.get_entry("u1") is None
    assert "u1" not in instance._local_entries


# 空列表等假值是合法缓存值，命中后回填本地键值
@pytest.mark.anyio
async def test_get_entry_treats_falsy_redis_payload_as_hit(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=False))
    fake_redis.get.return_value = []

    assert await instance.get_entry("u1") == []
    assert instance._local_entries["u1"][0] == []


# L2 读取抛异常时降级为未命中且不污染本地键值
@pytest.mark.anyio
async def test_get_entry_degrades_to_none_when_redis_read_fails(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=False))
    fake_redis.get.side_effect = RuntimeError("redis down")

    assert await instance.get_entry("u1") is None
    assert "u1" not in instance._local_entries


# 写入时落 L1、按前缀拼业务键写 L2 并提交版本号
@pytest.mark.anyio
async def test_set_entry_writes_prefixed_redis_key_and_commits_version(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    update_version = AsyncMock()
    monkeypatch.setattr(instance, "update_version", update_version)

    await instance.set_entry("u1", {"views": 2})

    fake_redis.set.assert_awaited_once_with("test:keyed:u1", {"views": 2}, ex=86400)
    assert instance._local_entries["u1"][0] == {"views": 2}
    update_version.assert_awaited_once()


# L2 写入失败只记录日志，L1 与版本号提交仍按流程完成
@pytest.mark.anyio
async def test_set_entry_keeps_local_value_when_redis_write_fails(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    fake_redis.set.side_effect = RuntimeError("redis down")
    update_version = AsyncMock()
    monkeypatch.setattr(instance, "update_version", update_version)

    await instance.set_entry("u1", {"views": 2})

    assert instance._local_entries["u1"][0] == {"views": 2}
    update_version.assert_awaited_once()


# 清空时按 SCAN 模式删除该前缀下的全部数据键并删除版本号键，重置本地状态
@pytest.mark.anyio
async def test_clear_all_deletes_prefixed_keys_by_scan_and_version(
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    instance._local_entries["u1"] = ({"views": 1}, time.time())
    instance._cache_version = "v1"

    await instance.clear_all()

    fake_redis.delete_by_patterns.assert_awaited_once_with("test:keyed:*")
    fake_redis.delete.assert_awaited_once_with("test:keyed:version")
    # KEYS 会阻塞 Redis，清空逻辑不再使用
    fake_redis.keys.assert_not_awaited()
    assert instance._local_entries == {}
    assert instance._cache_version is None


# Redis 扫描删除或删除版本号失败被吞掉，本地键值仍清空
@pytest.mark.anyio
async def test_clear_all_resets_local_state_when_redis_fails(
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    instance._local_entries["u1"] = ({"views": 1}, time.time())
    instance._cache_version = "v1"
    fake_redis.delete_by_patterns.side_effect = RuntimeError("redis down")

    await instance.clear_all()

    assert instance._local_entries == {}
    assert instance._cache_version is None


# 命中缓存时 get_entry_or_load 不执行回源
@pytest.mark.anyio
async def test_get_entry_or_load_returns_cached_without_loading(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, _ = cache
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=False))
    instance._local_entries["u1"] = ([], time.time())
    loader = AsyncMock(return_value=[{"views": 1}])

    assert await instance.get_entry_or_load("u1", loader) == []
    loader.assert_not_awaited()


# 未命中时执行回源并写入两级缓存
@pytest.mark.anyio
async def test_get_entry_or_load_loads_and_fills_on_miss(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=False))
    monkeypatch.setattr(instance, "update_version", AsyncMock())

    assert await instance.get_entry_or_load(
        "u1", AsyncMock(return_value={"views": 2})
    ) == {"views": 2}

    fake_redis.set.assert_awaited_once_with("test:keyed:u1", {"views": 2}, ex=86400)
    assert instance._local_entries["u1"][0] == {"views": 2}
    assert instance._single_flight.in_flight == 0


# 空结果回源后不写缓存，避免把空集固化为长期缓存
@pytest.mark.anyio
async def test_get_entry_or_load_skips_fill_for_empty_result(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=False))
    update_version = AsyncMock()
    monkeypatch.setattr(instance, "update_version", update_version)

    assert await instance.get_entry_or_load("u1", AsyncMock(return_value=[])) == []
    fake_redis.set.assert_not_awaited()
    update_version.assert_not_awaited()


# 同 key 并发未命中只回源一次
@pytest.mark.anyio
async def test_get_entry_or_load_merges_concurrent_misses(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, _ = cache
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=False))
    monkeypatch.setattr(instance, "update_version", AsyncMock())
    started = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    async def loader() -> dict[str, int]:
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()
        return {"views": 3}

    first = asyncio.create_task(instance.get_entry_or_load("u1", loader))
    await started.wait()
    second = asyncio.create_task(instance.get_entry_or_load("u1", loader))
    await asyncio.sleep(0)
    release.set()

    assert await asyncio.gather(first, second) == [{"views": 3}, {"views": 3}]
    assert calls == 1


# 回源异常向调用方传播并释放单飞 key
@pytest.mark.anyio
async def test_get_entry_or_load_propagates_loader_error(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, _ = cache
    monkeypatch.setattr(instance, "is_version_changed", AsyncMock(return_value=False))

    with pytest.raises(RuntimeError, match="db down"):
        await instance.get_entry_or_load(
            "u1", AsyncMock(side_effect=RuntimeError("db down"))
        )

    assert instance._single_flight.in_flight == 0


# 容量达到上限且写入新键时淘汰最早写入的条目
def test_write_local_evicts_oldest_entry_at_capacity(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, _ = cache
    monkeypatch.setattr(instance, "L1_MAX_ENTRIES", 2)
    instance._local_entries["u1"] = ({"views": 1}, 100.0)
    instance._local_entries["u2"] = ({"views": 2}, 200.0)

    instance._write_local("u3", {"views": 3})

    assert list(instance._local_entries) == ["u2", "u3"]


# 容量达到上限但覆盖已有键时不淘汰其它条目
def test_write_local_keeps_capacity_keys_when_overwriting_existing_key(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_KeyedCache, _FakeRedis],
) -> None:
    instance, _ = cache
    monkeypatch.setattr(instance, "L1_MAX_ENTRIES", 2)
    instance._local_entries["u1"] = ({"views": 1}, 100.0)
    instance._local_entries["u2"] = ({"views": 2}, 200.0)

    instance._write_local("u2", {"views": 20})

    assert set(instance._local_entries) == {"u1", "u2"}
    assert instance._local_entries["u2"][0] == {"views": 20}
