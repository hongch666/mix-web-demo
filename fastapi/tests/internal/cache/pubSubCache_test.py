import json
import time
from collections.abc import Generator
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.constants import RedisKeys
from app.internal.cache import (
    KeyedPubSubCache,
    baseCache as base_cache,
    pubSubCache as pub_sub_module,
)


class _FakeRedis:
    """最小 Redis 替身，记录读写、删除、按前缀列举与发布，不连接真实 Redis"""

    def __init__(self) -> None:
        self.get = AsyncMock(return_value=None)
        self.set = AsyncMock(return_value=True)
        self.delete = AsyncMock(return_value=True)
        self.keys = AsyncMock(return_value=[])
        self.publish = AsyncMock(return_value=True)
        self.get_pubsub = AsyncMock(return_value=None)
        self.get_many = AsyncMock(return_value={})
        self.set_many = AsyncMock(return_value=True)
        self.deleted_patterns: list[str] = []

    async def delete_by_patterns(self, *patterns: str) -> int:
        self.deleted_patterns.extend(patterns)
        return len(patterns)


class _TestCache(KeyedPubSubCache):
    """用于验证广播失效模板行为的最小实现"""

    REDIS_KEY_PREFIX: str = "test:pubsub:"
    INVALIDATION_NAMESPACE: str = "test"


class _OtherCache(KeyedPubSubCache):
    """另一个命名空间的最小实现，用于验证广播只清理匹配命名空间"""

    REDIS_KEY_PREFIX: str = "other:pubsub:"
    INVALIDATION_NAMESPACE: str = "other"


@pytest.fixture
def cache(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[tuple[_TestCache, _FakeRedis], None, None]:
    fake_redis = _FakeRedis()
    # BaseCache.__init__ 在 baseCache 模块解析 get_redis_client，
    # 订阅循环在 pubSubCache 模块解析，替身需要同时覆盖两处
    monkeypatch.setattr(base_cache, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(pub_sub_module, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(base_cache, "Logger", Mock())
    monkeypatch.setattr(pub_sub_module, "Logger", Mock())
    instance = _TestCache()
    yield instance, fake_redis
    pub_sub_module._broadcast_caches.clear()


# 写入应同时落本地与 Redis，且 Redis key 带前缀
@pytest.mark.anyio
async def test_set_entry_writes_both_levels(
    cache: tuple[_TestCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache

    await instance.set_entry("k", {"views": 1})

    assert instance._local_entries["test:k"][0] == {"views": 1}
    # 替身直接替换 RedisClient，JSON 序列化发生在包装层，此处收到的是原始值
    fake_redis.set.assert_awaited_once_with("test:pubsub:k", {"views": 1}, ex=86400)


# 本地命中时不再访问 Redis
@pytest.mark.anyio
async def test_get_entry_hits_local_skips_redis(
    cache: tuple[_TestCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    await instance.set_entry("k", {"views": 1})
    fake_redis.get.reset_mock()

    assert await instance.get_entry("k") == {"views": 1}
    fake_redis.get.assert_not_awaited()


# 本地未命中时读 Redis 并回填本地
@pytest.mark.anyio
async def test_get_entry_miss_loads_from_redis_and_backfills(
    cache: tuple[_TestCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    fake_redis.get = AsyncMock(return_value={"views": 2})

    assert await instance.get_entry("k") == {"views": 2}
    assert instance._local_entries["test:k"][0] == {"views": 2}


# 本地条目过期后不再返回旧值
@pytest.mark.anyio
async def test_local_entry_expires_after_ttl(
    cache: tuple[_TestCache, _FakeRedis],
) -> None:
    instance, _ = cache
    await instance.set_entry("k", {"views": 1})
    local_key = "test:k"
    value, _ = instance._local_entries[local_key]
    instance._local_entries[local_key] = (value, time.time() - 10_000)

    assert await instance.get_entry("k") is None


# 失效命名空间应清空 Redis 前缀键、清理本地并发布广播
@pytest.mark.anyio
async def test_invalidate_namespace_clears_and_broadcasts(
    cache: tuple[_TestCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    await instance.set_entry("k", {"views": 1})
    fake_redis.keys = AsyncMock(return_value=["test:pubsub:k"])
    fake_redis.publish.reset_mock()

    await instance.invalidate_namespace()

    fake_redis.delete.assert_awaited_once_with("test:pubsub:k")
    fake_redis.publish.assert_awaited_once_with(
        RedisKeys.CACHE_INVALIDATE_CHANNEL, '{"namespace": "test"}'
    )
    assert instance._local_entries == {}


# 广播发布失败只记录告警，不影响 Redis 键清理
@pytest.mark.anyio
async def test_invalidate_namespace_tolerates_publish_failure(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_TestCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    fake_redis.publish = AsyncMock(return_value=False)
    logger_mock = Mock()
    monkeypatch.setattr(instance, "_logger", logger_mock)

    await instance.invalidate_namespace()

    logger_mock.warning.assert_called_once()


# 收到匹配命名空间的广播时只清理对应实例的本地条目
@pytest.mark.anyio
async def test_broadcast_only_clears_matching_namespace(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_TestCache, _FakeRedis],
) -> None:
    instance, _ = cache
    other = _OtherCache()

    await instance.set_entry("k", {"views": 1})
    await other.set_entry("k", {"views": 2})

    pub_sub_module._handle_invalidation_message('{"namespace": "test"}')

    assert instance._local_entries == {}
    assert other._local_entries["other:k"][0] == {"views": 2}


# 非法广播内容解析失败不应抛出异常
@pytest.mark.anyio
async def test_broadcast_ignores_invalid_payload(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_TestCache, _FakeRedis],
) -> None:
    logger_mock = Mock()
    monkeypatch.setattr(pub_sub_module, "Logger", logger_mock)

    pub_sub_module._handle_invalidation_message(b"not-json")

    logger_mock.error.assert_called_once()


# 同一实例重复注册应被忽略
def test_duplicate_registration_ignored(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_TestCache, _FakeRedis],
) -> None:
    instance, _ = cache

    pub_sub_module.register_broadcast_cache(instance)

    assert pub_sub_module.get_broadcast_caches().count(instance) == 1


# 按文章 id 部分失效：只清理包含该 id 段的本地条目，并按通配模式删除 Redis 键
@pytest.mark.anyio
async def test_invalidate_ids_clears_matching_segments(
    cache: tuple[_TestCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    await instance.set_entry("tag_interest:7:3", [{"rawScore": 1}])
    await instance.set_entry("tag_interest:8:3", [{"rawScore": 2}])
    fake_redis.deleted_patterns.clear()

    await instance.invalidate_ids([7])

    assert instance._local_entries.get("test:tag_interest:7:3") is None
    assert instance._local_entries.get("test:tag_interest:8:3") is not None
    assert set(fake_redis.deleted_patterns) == {
        "test:pubsub:*:7",
        "test:pubsub:*:7:*",
    }
    payload = json.loads(fake_redis.publish.await_args.args[1])
    assert payload == {"namespace": "test", "ids": ["7"]}


# 按用户 id 部分失效：只清理以该用户 id 结尾的个性化条目
@pytest.mark.anyio
async def test_invalidate_user_ids_clears_matching_suffix(
    cache: tuple[_TestCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    await instance.set_entry("tag_interest:7:3", [{"rawScore": 1}])
    await instance.set_entry("keyword_tag:7:abc", [{"rawScore": 2}])
    fake_redis.deleted_patterns.clear()

    await instance.invalidate_user_ids([3])

    assert instance._local_entries.get("test:tag_interest:7:3") is None
    assert instance._local_entries.get("test:keyword_tag:7:abc") is not None
    assert fake_redis.deleted_patterns == ["test:pubsub:*:*:3"]
    payload = json.loads(fake_redis.publish.await_args.args[1])
    assert payload == {"namespace": "test", "user_ids": ["3"]}


# 广播携带 ids 时按 id 段精确清理本地条目
@pytest.mark.anyio
async def test_broadcast_with_ids_clears_matching_entries(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_TestCache, _FakeRedis],
) -> None:
    instance, _ = cache
    await instance.set_entry("tag_interest:7:3", [{"rawScore": 1}])
    await instance.set_entry("tag_interest:8:3", [{"rawScore": 2}])

    pub_sub_module._handle_invalidation_message('{"namespace": "test", "ids": ["7"]}')

    assert instance._local_entries.get("test:tag_interest:7:3") is None
    assert instance._local_entries.get("test:tag_interest:8:3") is not None


# 广播携带 user_ids 时按末段用户 id 清理个性化条目
@pytest.mark.anyio
async def test_broadcast_with_user_ids_clears_matching_entries(
    monkeypatch: pytest.MonkeyPatch,
    cache: tuple[_TestCache, _FakeRedis],
) -> None:
    instance, _ = cache
    await instance.set_entry("tag_interest:7:3", [{"rawScore": 1}])
    await instance.set_entry("keyword_tag:7:abc", [{"rawScore": 2}])

    pub_sub_module._handle_invalidation_message(
        '{"namespace": "test", "user_ids": ["3"]}'
    )

    assert instance._local_entries.get("test:tag_interest:7:3") is None
    assert instance._local_entries.get("test:keyword_tag:7:abc") is not None


# 批量读只发一次 mget，命中结果回填本地
@pytest.mark.anyio
async def test_get_entries_reads_redis_in_one_batch(
    cache: tuple[_TestCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    fake_redis.get_many = AsyncMock(
        return_value={"test:pubsub:a": [1], "test:pubsub:c": []}
    )

    result = await instance.get_entries(["a", "b", "c"])

    fake_redis.get_many.assert_awaited_once_with(
        ["test:pubsub:a", "test:pubsub:b", "test:pubsub:c"]
    )
    assert result == {"a": [1], "c": []}
    assert instance._local_entries["test:c"][0] == []


# 本地已命中时不访问 Redis
@pytest.mark.anyio
async def test_get_entries_skips_redis_when_all_local(
    cache: tuple[_TestCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache
    await instance.set_entry("a", [1])

    result = await instance.get_entries(["a"])

    assert result == {"a": [1]}
    fake_redis.get_many.assert_not_awaited()


# 批量写只发一次 set_many，并带上默认 TTL
@pytest.mark.anyio
async def test_set_entries_writes_redis_in_one_batch(
    cache: tuple[_TestCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache

    await instance.set_entries({"a": [1], "b": []})

    fake_redis.set_many.assert_awaited_once_with(
        {"test:pubsub:a": [1], "test:pubsub:b": []}, ex=86400
    )
    assert instance._local_entries["test:a"][0] == [1]


# 指定 TTL 时同时覆盖 L1 过期时间与 L2 过期秒数，用于空结果负缓存
@pytest.mark.anyio
async def test_set_entry_with_ttl_overrides_both_levels(
    cache: tuple[_TestCache, _FakeRedis],
) -> None:
    instance, fake_redis = cache

    await instance.set_entry("a", [], ttl=60)

    _, expires_at = instance._local_entries["test:a"]
    assert 0 < expires_at - time.time() <= 60
    fake_redis.set.assert_awaited_once_with("test:pubsub:a", [], ex=60)


# 失效频道按服务隔离，避免与 NestJS 的 key 列表消息格式互相干扰
def test_invalidate_channel_is_service_scoped() -> None:
    assert RedisKeys.CACHE_INVALIDATE_CHANNEL == "cache:invalidate:fastapi"


# Redis 不可用时订阅协程静默跳过且可安全停止
@pytest.mark.anyio
async def test_subscriber_skips_when_redis_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_redis = _FakeRedis()
    fake_redis.get_pubsub = AsyncMock(return_value=None)
    monkeypatch.setattr(base_cache, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(pub_sub_module, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(base_cache, "Logger", Mock())
    monkeypatch.setattr(pub_sub_module, "Logger", Mock())

    await pub_sub_module.start_cache_invalidation_subscriber()
    await pub_sub_module.stop_cache_invalidation_subscriber()

    assert pub_sub_module._subscriber_task is None
