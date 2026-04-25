import asyncio
import json
from typing import Any, Optional

import aio_pika
from app.core.base import Constants, Logger
from app.core.config import load_config


class RabbitMQClient:
    """RabbitMQ 客户端"""

    def __init__(self) -> None:
        """初始化 RabbitMQ 客户端"""
        self.connection: Optional[Any] = None
        self.channel: Optional[Any] = None
        self._is_connected: bool = False
        self._reconnect_delay: float = 1.0
        self._max_reconnect_delay: float = 30.0
        self._connection_lock: Optional[asyncio.Lock] = None

    async def _get_connection_lock(self) -> asyncio.Lock:
        if self._connection_lock is None:
            self._connection_lock = asyncio.Lock()
        return self._connection_lock

    async def _connect_async(self) -> None:
        """建立 RabbitMQ 连接"""
        if self._is_connected and self.connection and self.channel:
            if not getattr(self.connection, "is_closed", True) and not getattr(
                self.channel, "is_closed", True
            ):
                return

        connection_lock = await self._get_connection_lock()
        async with connection_lock:
            if self._is_connected and self.connection and self.channel:
                if not getattr(self.connection, "is_closed", True) and not getattr(
                    self.channel, "is_closed", True
                ):
                    return

            rabbitmq_config = load_config("rabbitmq")
            if not rabbitmq_config:
                Logger.warning(Constants.RABBITMQ_CONFIG_NOT_FOUND_MESSAGE)
                return

            host = str(rabbitmq_config.get("host", "127.0.0.1"))
            port = int(rabbitmq_config.get("port", 5672))
            username = str(rabbitmq_config.get("username", "guest"))
            password = str(rabbitmq_config.get("password", "guest"))
            vhost = str(rabbitmq_config.get("vhost", "/"))

            try:
                self.connection = await aio_pika.connect_robust(
                    host=host,
                    port=port,
                    login=username,
                    password=password,
                    virtualhost=vhost,
                    heartbeat=60,
                    connection_attempts=3,
                    retry_delay=1.0,
                    timeout=10,
                )
                self.channel = await self.connection.channel()
                self._is_connected = True
                self._reconnect_delay = 1.0
                Logger.info(f"RabbitMQ 连接成功: {host}:{port}")
            except Exception as e:
                self._is_connected = False
                self.connection = None
                self.channel = None
                Logger.warning(f"RabbitMQ 连接失败: {e}")

    async def _close_async(self) -> None:
        try:
            if self.channel and not getattr(self.channel, "is_closed", True):
                await self.channel.close()
            if self.connection and not getattr(self.connection, "is_closed", True):
                await self.connection.close()
        finally:
            self.connection = None
            self.channel = None
            self._is_connected = False

    async def send_message_async(
        self, queue_name: str, message: Any, persistent: bool = True
    ) -> bool:
        """异步发送消息到指定队列。"""
        max_retries: int = 3
        for attempt in range(max_retries):
            try:
                await self._connect_async()

                if not self._is_connected or self.channel is None:
                    Logger.error(Constants.RABBITMQ_NOT_CONNECTED_MESSAGE)
                    return False

                await self.channel.declare_queue(queue_name, durable=True)

                if isinstance(message, dict):
                    message_body = json.dumps(message, ensure_ascii=False)
                else:
                    message_body = str(message)

                delivery_mode = (
                    aio_pika.DeliveryMode.PERSISTENT
                    if persistent
                    else aio_pika.DeliveryMode.NOT_PERSISTENT
                )
                rabbitmq_message = aio_pika.Message(
                    body=message_body.encode("utf-8"),
                    delivery_mode=delivery_mode,
                    content_type="application/json",
                )
                await self.channel.default_exchange.publish(
                    rabbitmq_message, routing_key=queue_name
                )

                Logger.info(f"消息已发送到队列 [{queue_name}]: {message_body[:100]}...")
                return True

            except Exception as e:
                Logger.warning(
                    f"发送消息到队列 [{queue_name}] 失败（第 {attempt + 1} 次尝试）: {e}"
                )
                self._is_connected = False
                await self._close_async()
                if attempt < max_retries - 1:
                    await asyncio.sleep(
                        min(self._reconnect_delay, self._max_reconnect_delay)
                    )
                    self._reconnect_delay = min(
                        self._reconnect_delay * 2, self._max_reconnect_delay
                    )
                    continue

                Logger.error(f"发送消息到队列 [{queue_name}] 失败：达到最大重试次数")
                return False

        return False

    async def close_async(self) -> None:
        """关闭连接"""
        try:
            await self._close_async()
            Logger.info(Constants.RABBITMQ_CONNECTION_CLOSED_MESSAGE)
        except Exception as e:
            Logger.error(f"关闭 RabbitMQ 连接失败: {e}")

    def close(self) -> None:
        """同步关闭连接"""
        try:
            asyncio.get_running_loop()
            Logger.warning(Constants.AIO_PKA_EVENT_LOOP_ERROR)
        except RuntimeError:
            asyncio.run(self.close_async())

    def __del__(self) -> None:
        """析构函数，确保连接关闭"""
        try:
            self.close()
        except Exception:
            pass


# 全局 RabbitMQ 客户端实例
_rabbitmq_client: Optional[RabbitMQClient] = None


def get_rabbitmq_client() -> Optional[RabbitMQClient]:
    """获取全局 RabbitMQ 客户端实例（单例模式）"""
    global _rabbitmq_client
    if _rabbitmq_client is None:
        try:
            _rabbitmq_client = RabbitMQClient()
        except Exception as e:
            Logger.error(f"初始化 RabbitMQ 客户端失败: {e}")
            return None
    return _rabbitmq_client


async def send_to_queue_async(
    queue_name: str, message: Any, persistent: bool = True
) -> bool:
    """异步发送消息到队列。"""
    try:
        client = get_rabbitmq_client()
        if client is None:
            Logger.warning(Constants.RABBITMQ_CLIENT_NOT_INITIALIZED_MESSAGE)
            return False
        return await client.send_message_async(queue_name, message, persistent)
    except Exception as e:
        Logger.error(f"发送消息失败: {e}")
        return False
