import json
from typing import Any

import pytest

from app.core.db import rabbitmq as rabbitmq_module, send_to_queue_async

_RABBITMQ_CONFIG: dict[str, Any] = {
    "host": "mq.internal",
    "port": 5672,
    "username": "demo",
    "password": "unit-test-secret",
    "vhost": "/test",
}


class _FakeCallbacks:
    """替代 aio_pika 的重连回调集合"""

    def __init__(self) -> None:
        self.callbacks: list[Any] = []

    def add(self, callback: Any) -> None:
        self.callbacks.append(callback)


class _FakeChannel:
    """替代 aio_pika 通道边界，记录队列声明与发布，不连接真实 Broker"""

    def __init__(self, is_closed: bool = False) -> None:
        self.is_closed = is_closed
        self.declared: list[tuple[str, bool]] = []
        self.published: list[tuple[Any, str]] = []
        self.close_calls = 0
        self.default_exchange = self

    async def declare_queue(self, name: str, durable: bool = False) -> None:
        self.declared.append((name, durable))

    async def publish(self, message: Any, routing_key: str) -> None:
        self.published.append((message, routing_key))

    async def close(self) -> None:
        self.close_calls += 1
        self.is_closed = True


class _FakeConnection:
    """替代 aio_pika RobustConnection 边界"""

    def __init__(self, is_closed: bool = False) -> None:
        self.is_closed = is_closed
        self.channels: list[_FakeChannel] = []
        self.reconnect_callbacks = _FakeCallbacks()
        self.close_calls = 0

    async def channel(self) -> _FakeChannel:
        channel = _FakeChannel()
        self.channels.append(channel)
        return channel

    async def close(self) -> None:
        self.close_calls += 1
        self.is_closed = True


class _StubClient:
    """记录转发参数的客户端替身"""

    def __init__(self) -> None:
        self.calls: list[tuple[str, Any, bool]] = []

    async def send_message_async(
        self, queue_name: str, message: Any, persistent: bool = True
    ) -> bool:
        self.calls.append((queue_name, message, persistent))
        return True


def _patch_config(monkeypatch: pytest.MonkeyPatch, config: Any) -> None:
    monkeypatch.setattr(rabbitmq_module, "load_config", lambda section: config)


def _patch_connect(monkeypatch: pytest.MonkeyPatch, outcome: Any) -> dict[str, Any]:
    """把 connect_robust 替换为假实现，并记录调用参数"""
    captured: dict[str, Any] = {}

    async def fake_connect_robust(url: str, **kwargs: Any) -> Any:
        captured["url"] = url
        captured["kwargs"] = kwargs
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(rabbitmq_module.aio_pika, "connect_robust", fake_connect_robust)
    return captured


# 配置段缺失时返回 None 并给出告警，不抛出连接异常
def test_build_url_returns_none_without_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_config(monkeypatch, None)
    warnings: list[str] = []
    monkeypatch.setattr(rabbitmq_module.Logger, "warning", warnings.append)

    assert rabbitmq_module.RabbitMQClient()._build_url() is None
    assert warnings


# vhost 前导斜杠被剥离后拼出 amqp 地址
def test_build_url_strips_leading_slash_of_vhost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_config(monkeypatch, dict(_RABBITMQ_CONFIG))

    assert (
        rabbitmq_module.RabbitMQClient()._build_url()
        == "amqp://demo:unit-test-secret@mq.internal:5672/test"
    )


# 连接可用时直接返回，不重复建立连接
@pytest.mark.anyio
async def test_connect_skips_when_connection_alive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _patch_connect(monkeypatch, _FakeConnection())
    client = rabbitmq_module.RabbitMQClient()
    client.connection = _FakeConnection(is_closed=False)

    assert await client.connect() is True
    assert captured == {}


# 配置缺失导致 url 为空时判定连接失败
@pytest.mark.anyio
async def test_connect_returns_false_without_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_config(monkeypatch, None)

    assert await rabbitmq_module.RabbitMQClient().connect() is False


# 连接成功后保存连接与通道，并注册重连回调
@pytest.mark.anyio
async def test_connect_registers_reconnect_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = _FakeConnection()
    captured = _patch_connect(monkeypatch, connection)
    _patch_config(monkeypatch, dict(_RABBITMQ_CONFIG))
    client = rabbitmq_module.RabbitMQClient()

    assert await client.connect() is True
    assert captured["url"] == "amqp://demo:unit-test-secret@mq.internal:5672/test"
    assert captured["kwargs"]["heartbeat"] == 60
    assert client.connection is connection
    assert client.channel is connection.channels[0]
    assert connection.reconnect_callbacks.callbacks == [client._on_reconnect]
    await client.close_async()


# 建连异常时返回 False 且不残留连接引用
@pytest.mark.anyio
async def test_connect_returns_false_on_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_connect(monkeypatch, OSError("connection refused"))
    _patch_config(monkeypatch, dict(_RABBITMQ_CONFIG))
    warnings: list[str] = []
    monkeypatch.setattr(rabbitmq_module.Logger, "warning", warnings.append)
    client = rabbitmq_module.RabbitMQClient()

    assert await client.connect() is False
    assert warnings
    assert client.connection is None


# 重连回调重新获取通道，连接缺失时只告警不抛错
@pytest.mark.anyio
async def test_on_reconnect_recovers_channel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    warnings: list[str] = []
    monkeypatch.setattr(rabbitmq_module.Logger, "warning", warnings.append)
    client = rabbitmq_module.RabbitMQClient()

    await client._on_reconnect(object())

    assert warnings
    assert client.channel is None

    connection = _FakeConnection()
    client.connection = connection

    await client._on_reconnect(object())

    assert client.channel is connection.channels[0]
    await client.close_async()


# 未连接或连接已关闭时发送直接失败
@pytest.mark.anyio
async def test_send_message_fails_without_usable_connection() -> None:
    client = rabbitmq_module.RabbitMQClient()

    assert await client.send_message_async("api-log-queue", {"a": 1}) is False

    client.connection = _FakeConnection(is_closed=True)
    client.channel = _FakeChannel()

    assert await client.send_message_async("api-log-queue", {"a": 1}) is False


# 字典消息序列化为 JSON，并按持久化模式投递到目标队列
@pytest.mark.anyio
async def test_send_message_publishes_json_payload() -> None:
    client = rabbitmq_module.RabbitMQClient()
    client.connection = _FakeConnection()
    channel = _FakeChannel()
    client.channel = channel

    sent: bool = await client.send_message_async(
        "api-log-queue", {"userId": 1}, persistent=True
    )

    assert sent is True
    assert channel.declared == [("api-log-queue", True)]
    message, routing_key = channel.published[0]
    assert routing_key == "api-log-queue"
    assert json.loads(message.body.decode("utf-8")) == {"userId": 1}
    assert message.delivery_mode == rabbitmq_module.aio_pika.DeliveryMode.PERSISTENT
    await client.close_async()


# 非字典消息按字符串发送，非持久化模式可选
@pytest.mark.anyio
async def test_send_message_supports_plain_text_and_transient_mode() -> None:
    client = rabbitmq_module.RabbitMQClient()
    client.connection = _FakeConnection()
    channel = _FakeChannel()
    client.channel = channel

    sent: bool = await client.send_message_async(
        "article-log-queue", "plain", persistent=False
    )

    assert sent is True
    message, _ = channel.published[0]
    assert message.body == b"plain"
    assert message.delivery_mode == rabbitmq_module.aio_pika.DeliveryMode.NOT_PERSISTENT
    await client.close_async()


# 发布异常被吞掉并返回 False，不影响调用方主流程
@pytest.mark.anyio
async def test_send_message_returns_false_on_publish_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = rabbitmq_module.RabbitMQClient()
    client.connection = _FakeConnection()
    channel = _FakeChannel()

    async def failing_publish(message: Any, routing_key: str) -> None:
        raise OSError("channel closed")

    channel.publish = failing_publish
    client.channel = channel
    warnings: list[str] = []
    monkeypatch.setattr(rabbitmq_module.Logger, "warning", warnings.append)

    assert await client.send_message_async("api-log-queue", {"a": 1}) is False
    assert warnings


# 关闭连接时关闭通道与连接并清空引用
@pytest.mark.anyio
async def test_close_async_clears_references() -> None:
    client = rabbitmq_module.RabbitMQClient()
    connection = _FakeConnection()
    channel = _FakeChannel()
    client.connection = connection
    client.channel = channel

    await client.close_async()

    assert channel.close_calls == 1
    assert connection.close_calls == 1
    assert client.channel is None
    assert client.connection is None


# 全局客户端按单例返回
def test_get_rabbitmq_client_is_singleton(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rabbitmq_module, "_rabbitmq_client", None)

    first = rabbitmq_module.get_rabbitmq_client()
    second = rabbitmq_module.get_rabbitmq_client()

    assert first is second
    assert isinstance(first, rabbitmq_module.RabbitMQClient)


# 未初始化客户端时发送直接失败
@pytest.mark.anyio
async def test_send_to_queue_async_without_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rabbitmq_module, "get_rabbitmq_client", lambda: None)

    assert await send_to_queue_async("api-log-queue", {"a": 1}) is False


# 已初始化客户端时转发队列名、消息与持久化标记
@pytest.mark.anyio
async def test_send_to_queue_async_forwards_to_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _StubClient()
    monkeypatch.setattr(rabbitmq_module, "get_rabbitmq_client", lambda: stub)

    assert await send_to_queue_async("api-log-queue", {"a": 1}, False) is True
    assert stub.calls == [("api-log-queue", {"a": 1}, False)]
