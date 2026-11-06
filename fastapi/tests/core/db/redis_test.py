import json
from collections.abc import AsyncIterator
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.core.constants import Defaults
from app.core.db import RedisClient, redis as redis_module

_REDIS_CONFIG: dict[str, Any] = {
    "host": "127.0.0.1",
    "port": 6379,
    "db": 4,
    "decode_responses": True,
    "max_connections": 10,
}


def _new_client(
    monkeypatch: pytest.MonkeyPatch,
    redis_config: dict[str, Any] | None = None,
) -> RedisClient:
    """用假配置构造客户端，绕开单例缓存与真实配置读取"""
    selected: dict[str, Any] = (
        dict(_REDIS_CONFIG) if redis_config is None else redis_config
    )
    monkeypatch.setattr(
        redis_module, "load_config", lambda section: {"redis": selected}
    )
    monkeypatch.setattr(redis_module.RedisClient, "_instance", None)
    monkeypatch.setattr(redis_module, "_redis_client", None)
    return redis_module.RedisClient()


def _new_client_without_config(monkeypatch: pytest.MonkeyPatch) -> RedisClient:
    """模拟配置读取失败：客户端进入降级状态"""

    def raising_loader(section: str) -> Any:
        raise KeyError("database")

    monkeypatch.setattr(redis_module, "load_config", raising_loader)
    monkeypatch.setattr(redis_module.RedisClient, "_instance", None)
    monkeypatch.setattr(redis_module, "_redis_client", None)
    return redis_module.RedisClient()


# 非 JSON 原生类型按约定转换：Decimal 取数值、日期走 ISO 格式、其余转字符串
def test_json_default_converts_non_serializable_types(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _new_client(monkeypatch)

    assert client._json_default(Decimal("3")) == 3
    assert client._json_default(Decimal("3.5")) == 3.5
    assert client._json_default(datetime(2026, 10, 15, 12, 0, 0)) == (
        "2026-10-15T12:00:00"
    )
    assert client._json_default(date(2026, 10, 15)) == "2026-10-15"
    assert isinstance(client._json_default(object()), str)


# 连接池参数固定携带超时配置，未配置用户名密码时不写入对应键
def test_build_pool_params_omits_empty_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _new_client(monkeypatch)

    params: dict[str, Any] = client._build_pool_params()

    assert params == {
        "host": "127.0.0.1",
        "port": 6379,
        "db": 4,
        "decode_responses": True,
        "max_connections": 10,
        "socket_connect_timeout": 5,
        "socket_timeout": 5,
    }


# 配置了用户名密码时一并写入连接池参数
def test_build_pool_params_includes_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _new_client(
        monkeypatch,
        {**_REDIS_CONFIG, "username": "demo", "password": "unit-test-secret"},
    )

    params: dict[str, Any] = client._build_pool_params()

    assert params["username"] == "demo"
    assert params["password"] == "unit-test-secret"


# 配置读取失败时降级：不建立客户端并记录错误，读写返回默认值
@pytest.mark.anyio
async def test_client_degrades_when_config_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    errors: list[str] = []
    monkeypatch.setattr(redis_module.Logger, "error", errors.append)

    client = _new_client_without_config(monkeypatch)

    assert errors
    assert client.get_client() is None
    assert await client._ensure_client() is None
    assert await client.is_available() is False
    assert await client.get("k") is None
    assert await client.set("k", "v") is False
    assert await client.delete("k") is False
    assert await client.exists("k") is False
    assert await client.expire("k", 60) is False
    assert await client.ttl("k") == -2
    assert await client.keys("*") == []
    assert await client.flushdb() is False
    assert await client.try_lock("lock:task", 30) is None
    assert await client.unlock("lock:task", "value") is True


# 读取时优先按 JSON 解析，解析失败则原样返回字符串
@pytest.mark.anyio
async def test_get_parses_json_and_falls_back_to_raw_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _new_client(monkeypatch)
    fake = AsyncMock()
    monkeypatch.setattr(client, "_ensure_client", AsyncMock(return_value=fake))

    fake.get.return_value = json.dumps({"a": 1})
    assert await client.get("k") == {"a": 1}

    fake.get.return_value = "plain"
    assert await client.get("k") == "plain"

    fake.get.return_value = None
    assert await client.get("k") is None


# 写入字典或列表时序列化为 JSON，并透传过期时间
@pytest.mark.anyio
async def test_set_serializes_container_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _new_client(monkeypatch)
    fake = AsyncMock()
    monkeypatch.setattr(client, "_ensure_client", AsyncMock(return_value=fake))

    assert await client.set("k", {"a": 1}, ex=60) is True
    fake.set.assert_awaited_once_with("k", '{"a": 1}', ex=60)

    assert await client.set("k2", [1, 2]) is True
    assert fake.set.await_args.args == ("k2", "[1, 2]")


# 键枚举、过期与清库按返回值语义转换
@pytest.mark.anyio
async def test_keys_expire_and_flush_translate_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _new_client(monkeypatch)
    fake = AsyncMock()
    monkeypatch.setattr(client, "_ensure_client", AsyncMock(return_value=fake))

    fake.exists.return_value = 1
    assert await client.exists("k") is True

    fake.exists.return_value = 0
    assert await client.exists("k") is False

    fake.expire.return_value = 1
    assert await client.expire("k", 60) is True

    fake.keys.return_value = ["a", "b"]
    assert await client.keys("*") == ["a", "b"]

    assert await client.flushdb() is True


# 加锁使用 SET NX EX 原子操作，锁值随机且与写入值一致
@pytest.mark.anyio
async def test_try_lock_uses_set_nx_ex(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _new_client(monkeypatch)
    fake = AsyncMock()
    fake.set.return_value = True
    monkeypatch.setattr(client, "_ensure_client", AsyncMock(return_value=fake))

    lock_value: str | None = await client.try_lock("lock:task", 30)

    assert lock_value is not None
    assert fake.set.await_args.args == ("lock:task", lock_value)
    assert fake.set.await_args.kwargs == {"ex": 30, "nx": True}


# 已被占用时返回 None，调用方据此判定未拿到锁
@pytest.mark.anyio
async def test_try_lock_returns_none_when_already_locked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _new_client(monkeypatch)
    fake = AsyncMock()
    fake.set.return_value = None
    monkeypatch.setattr(client, "_ensure_client", AsyncMock(return_value=fake))

    assert await client.try_lock("lock:task", 30) is None


# 解锁只认 Lua 脚本返回 1，其余结果视为释放失败
@pytest.mark.anyio
async def test_unlock_accepts_only_script_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _new_client(monkeypatch)
    fake = AsyncMock()
    monkeypatch.setattr(client, "_ensure_client", AsyncMock(return_value=fake))

    fake.eval.return_value = 1
    assert await client.unlock("lock:task", "value") is True

    fake.eval.return_value = 0
    assert await client.unlock("lock:task", "value") is False

    assert fake.eval.await_args.args[1:] == (1, "lock:task", "value")


class _FakeKeyspace:
    """最小 Redis 键空间替身：按模式产出键并记录每批删除的键"""

    def __init__(self, keys_by_pattern: dict[str, list[str]]) -> None:
        self._keys_by_pattern = keys_by_pattern
        self.scan_calls: list[dict[str, Any]] = []
        self.deleted_batches: list[list[str]] = []
        self.delete = AsyncMock(side_effect=self._delete)

    def scan_iter(self, match: str, count: int | None = None) -> AsyncIterator[str]:
        """按模式返回异步键迭代器，并记录扫描参数"""
        self.scan_calls.append({"match": match, "count": count})
        keys: list[str] = list(self._keys_by_pattern.get(match, []))

        async def iterator() -> AsyncIterator[str]:
            for key in keys:
                yield key

        return iterator()

    async def _delete(self, *keys: str) -> int:
        """记录一批删除并返回删除数量"""
        self.deleted_batches.append(list(keys))
        return len(keys)


# 命中键按批 DEL：一批最多 DEFAULT 个键，避免单条命令参数过多阻塞主线程
@pytest.mark.anyio
async def test_delete_by_patterns_deletes_in_batches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _new_client(monkeypatch)
    fake = _FakeKeyspace({"cache:a:*": [f"cache:a:{index}" for index in range(1200)]})
    monkeypatch.setattr(client, "_ensure_client", AsyncMock(return_value=fake))
    monkeypatch.setattr(Defaults, "REDIS_SCAN_DELETE_BATCH_SIZE", 500)

    assert await client.delete_by_patterns("cache:a:*") == 1200
    assert [len(batch) for batch in fake.deleted_batches] == [500, 500, 200]
    # COUNT 用批大小，减少 SCAN 往返次数
    assert fake.scan_calls == [{"match": "cache:a:*", "count": 500}]


# 没有匹配键时不发起 DEL
@pytest.mark.anyio
async def test_delete_by_patterns_skips_delete_when_no_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _new_client(monkeypatch)
    fake = _FakeKeyspace({})
    monkeypatch.setattr(client, "_ensure_client", AsyncMock(return_value=fake))

    assert await client.delete_by_patterns("cache:none:*") == 0
    fake.delete.assert_not_awaited()


# 多个模式的命中键共用同一批缓冲，跨模式攒满一批再删
@pytest.mark.anyio
async def test_delete_by_patterns_batches_across_patterns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _new_client(monkeypatch)
    fake = _FakeKeyspace(
        {
            "p1:*": [f"p1:{index}" for index in range(300)],
            "p2:*": [f"p2:{index}" for index in range(300)],
        }
    )
    monkeypatch.setattr(client, "_ensure_client", AsyncMock(return_value=fake))
    monkeypatch.setattr(Defaults, "REDIS_SCAN_DELETE_BATCH_SIZE", 500)

    assert await client.delete_by_patterns("p1:*", "p2:*") == 600
    assert [len(batch) for batch in fake.deleted_batches] == [500, 100]
    assert [call["match"] for call in fake.scan_calls] == ["p1:*", "p2:*"]


# Redis 不可用时按 0 处理且不报错
@pytest.mark.anyio
async def test_delete_by_patterns_returns_zero_without_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _new_client(monkeypatch)
    monkeypatch.setattr(client, "_ensure_client", AsyncMock(return_value=None))

    assert await client.delete_by_patterns("cache:a:*") == 0


# 中途失败时记录错误并返回已删除数量，不再继续后续批次
@pytest.mark.anyio
async def test_delete_by_patterns_returns_partial_count_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _new_client(monkeypatch)
    fake = _FakeKeyspace({"p:*": ["p:1", "p:2", "p:3"]})
    fake.delete.side_effect = [1, RuntimeError("redis down")]
    monkeypatch.setattr(client, "_ensure_client", AsyncMock(return_value=fake))
    monkeypatch.setattr(Defaults, "REDIS_SCAN_DELETE_BATCH_SIZE", 1)
    errors: list[str] = []
    monkeypatch.setattr(redis_module.Logger, "error", errors.append)

    assert await client.delete_by_patterns("p:*") == 1
    assert errors
    # 第一批成功、第二批抛错后停止，不再尝试剩余批次
    assert fake.delete.await_count == 2


# 全局客户端按单例返回
def test_get_redis_client_is_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        redis_module, "load_config", lambda section: {"redis": dict(_REDIS_CONFIG)}
    )
    monkeypatch.setattr(redis_module.RedisClient, "_instance", None)
    monkeypatch.setattr(redis_module, "_redis_client", None)

    assert redis_module.get_redis_client() is redis_module.get_redis_client()
