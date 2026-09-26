import hashlib
from collections.abc import Generator
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.constants import Scripts
from app.internal.cache import baseCache as base_cache
from app.internal.cache import versionedCache as versioned_cache
from app.internal.cache.versionedCache import VersionedCache


class _FakeRedis:
    """最小 Redis 替身，记录读写调用，不连接真实 Redis"""

    def __init__(self) -> None:
        self.get = AsyncMock(return_value=None)
        self.set = AsyncMock(return_value=True)
        self.delete = AsyncMock(return_value=True)


class _FakeTable:
    fullname: str = "warehouse.ads_top10_articles"


class _FakeModel:
    __table__ = _FakeTable()


class _VersionedCache(VersionedCache):
    """用于验证版本号逻辑的最小实现"""

    REDIS_KEY_PREFIX: str = "test:versioned:data"
    REDIS_VERSION_KEY: str = "test:versioned:version"
    VERSION_MODEL = _FakeModel

    async def get(self) -> object:
        return await self.get_from_local()

    async def set(self, data: object) -> None:
        await self.update_local_cache(data)


@pytest.fixture(autouse=True)
def _isolate_read_versions() -> Generator[None, None, None]:
    versioned_cache._READ_VERSIONS.set(None)
    yield
    versioned_cache._READ_VERSIONS.set(None)


@pytest.fixture
def cache(monkeypatch: pytest.MonkeyPatch) -> tuple[_VersionedCache, _FakeRedis]:
    fake_redis = _FakeRedis()
    monkeypatch.setattr(base_cache, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(base_cache, "Logger", Mock())
    monkeypatch.setattr(versioned_cache, "Logger", Mock())
    return _VersionedCache(), fake_redis


# 未配置 VERSION_MODEL 时直接返回 None 且不发起 ClickHouse 查询
@pytest.mark.anyio
async def test_get_cache_version_returns_none_when_model_not_set(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_VersionedCache, _FakeRedis],
) -> None:
    instance, _ = cache
    monkeypatch.setattr(type(instance), "VERSION_MODEL", None)
    query = AsyncMock()
    monkeypatch.setattr(versioned_cache, "execute_clickhouse_query", query)

    assert await instance.get_cache_version() is None
    query.assert_not_awaited()


# 用表名与统计行数据拼接后取 MD5 前 8 位作为版本号
@pytest.mark.anyio
async def test_get_cache_version_builds_stable_md5_from_table_stats(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_VersionedCache, _FakeRedis],
) -> None:
    instance, _ = cache
    query = AsyncMock(return_value=[(10, 1_700_000_000)])
    monkeypatch.setattr(versioned_cache, "execute_clickhouse_query", query)

    expected = hashlib.md5(b"warehouse.ads_top10_articles:10:1700000000").hexdigest()[
        :8
    ]

    assert await instance.get_cache_version() == expected
    query.assert_awaited_once_with(
        Scripts.CACHE_VERSION_CLICKHOUSE_QUERY("warehouse.ads_top10_articles")
    )


# ClickHouse 查询无结果行时版本号返回 None
@pytest.mark.anyio
async def test_get_cache_version_returns_none_when_query_returns_no_rows(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_VersionedCache, _FakeRedis],
) -> None:
    instance, _ = cache
    monkeypatch.setattr(
        versioned_cache, "execute_clickhouse_query", AsyncMock(return_value=[])
    )

    assert await instance.get_cache_version() is None


# ClickHouse 查询抛异常时版本号降级返回 None
@pytest.mark.anyio
async def test_get_cache_version_returns_none_when_query_fails(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_VersionedCache, _FakeRedis],
) -> None:
    instance, _ = cache
    monkeypatch.setattr(
        versioned_cache,
        "execute_clickhouse_query",
        AsyncMock(side_effect=RuntimeError("clickhouse down")),
    )

    assert await instance.get_cache_version() is None


# 当前版本号缺失时跳过校验返回 False 且不写版本键
@pytest.mark.anyio
async def test_is_version_changed_skips_when_current_version_missing(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_VersionedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "get_cache_version", AsyncMock(return_value=None))

    assert await instance.is_version_changed() is False
    fake_redis.set.assert_not_awaited()


# 版本键不存在时首次写入当前版本并判定未变化
@pytest.mark.anyio
async def test_is_version_changed_initializes_version_on_first_call(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_VersionedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "get_cache_version", AsyncMock(return_value="v1"))
    fake_redis.get.return_value = None

    assert await instance.is_version_changed() is False

    fake_redis.set.assert_awaited_once_with("test:versioned:version", "v1", ex=86400)
    assert instance._cache_version == "v1"


# Redis 版本与当前版本一致时判定未变化且不回写
@pytest.mark.anyio
async def test_is_version_changed_returns_false_when_version_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_VersionedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "get_cache_version", AsyncMock(return_value="v1"))
    fake_redis.get.return_value = "v1"

    assert await instance.is_version_changed() is False
    fake_redis.set.assert_not_awaited()


# Redis 版本与当前版本不一致时判定已变化
@pytest.mark.anyio
async def test_is_version_changed_returns_true_when_version_differs(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_VersionedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "get_cache_version", AsyncMock(return_value="v2"))
    fake_redis.get.return_value = "v1"

    assert await instance.is_version_changed() is True


# Redis 返回 bytes 版本值时解码后比较判定未变化
@pytest.mark.anyio
async def test_is_version_changed_decodes_bytes_old_version(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_VersionedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "get_cache_version", AsyncMock(return_value="v1"))
    fake_redis.get.return_value = b"v1"

    assert await instance.is_version_changed() is False


# Redis 读取失败时退化为本地版本比较，一致/不一致分别返回 False/True
@pytest.mark.anyio
@pytest.mark.parametrize(
    ("local_version", "expected"),
    [("v1", False), ("v0", True)],
)
async def test_is_version_changed_falls_back_to_local_version(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_VersionedCache, _FakeRedis],
    local_version: str,
    expected: bool,
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "get_cache_version", AsyncMock(return_value="v1"))
    fake_redis.get.side_effect = RuntimeError("redis down")
    instance._cache_version = local_version

    assert await instance.is_version_changed() is expected


# 版本查询抛异常时按未变化处理返回 False
@pytest.mark.anyio
async def test_is_version_changed_returns_false_when_query_raises(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_VersionedCache, _FakeRedis],
) -> None:
    instance, _ = cache
    monkeypatch.setattr(
        instance, "get_cache_version", AsyncMock(side_effect=RuntimeError("boom"))
    )

    assert await instance.is_version_changed() is False


# 存在已观测读版本时优先持久化该版本且取出后即消费
@pytest.mark.anyio
async def test_update_version_commits_observed_read_version(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_VersionedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    instance._remember_read_version("observed")
    live = AsyncMock(return_value="live")
    monkeypatch.setattr(instance, "get_cache_version", live)

    await instance.update_version()

    fake_redis.set.assert_awaited_once_with(
        "test:versioned:version", "observed", ex=86400
    )
    live.assert_not_awaited()
    assert instance._cache_version == "observed"
    # 读取版本已被消费，避免被后续无关写入复用
    assert instance._take_read_version() is None


# 无已观测版本时回退持久化实时查询到的版本号
@pytest.mark.anyio
async def test_update_version_falls_back_to_live_version(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_VersionedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "get_cache_version", AsyncMock(return_value="live"))

    await instance.update_version()

    fake_redis.set.assert_awaited_once_with("test:versioned:version", "live", ex=86400)


# 版本号不可用时跳过持久化不写 Redis
@pytest.mark.anyio
async def test_update_version_skips_persist_when_version_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_VersionedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    monkeypatch.setattr(instance, "get_cache_version", AsyncMock(return_value=None))

    await instance.update_version()

    fake_redis.set.assert_not_awaited()


# 版本持久化失败被吞掉但仍发起写入
@pytest.mark.anyio
async def test_update_version_swallows_persist_failure(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_VersionedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    fake_redis.set.side_effect = RuntimeError("redis down")
    monkeypatch.setattr(instance, "get_cache_version", AsyncMock(return_value="live"))

    await instance.update_version()

    fake_redis.set.assert_awaited_once()


# 读版本按 Redis 版本键存储，取出一次后即被清空
def test_read_version_is_scoped_per_redis_version_key(
    cache: tuple[_VersionedCache, _FakeRedis],
) -> None:
    instance, _ = cache

    instance._remember_read_version("v1")

    assert instance._take_read_version() == "v1"
    assert instance._take_read_version() is None


# 整体清空重置 L1 与版本缓存并按序删除数据键和版本键
@pytest.mark.anyio
async def test_clear_all_resets_version_and_deletes_both_keys(
    cache: tuple[_VersionedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache

    await instance.update_local_cache([{"id": 1}])
    instance._cache_version = "v1"
    await instance.clear_all()

    assert instance._local_cache is None
    assert instance._cache_version is None
    deleted = [call.args[0] for call in fake_redis.delete.await_args_list]
    assert deleted == ["test:versioned:data", "test:versioned:version"]


# 版本键删除失败被吞掉但两键删除均被发起
@pytest.mark.anyio
async def test_clear_all_swallows_version_delete_failure(
    cache: tuple[_VersionedCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    fake_redis.delete.side_effect = RuntimeError("redis down")

    await instance.clear_all()

    assert instance._cache_version is None
    assert fake_redis.delete.await_count == 2
