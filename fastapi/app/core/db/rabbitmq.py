import asyncio
import json
from typing import Any, Dict, Optional

import aio_pika
from app.core.base import Logger
from app.core.config import load_config
from app.core.constants import Messages


class RabbitMQClient:
    """RabbitMQ 客户端"""

    def __init__(self) -> None:
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None

    def _build_url(self) -> Optional[str]:
        """构建 AMQP 连接 URL"""
        config: Dict[str, Any] = load_config("rabbitmq")
        if not config:
            Logger.warning(Messages.RABBITMQ_CONFIG_NOT_FOUND_MESSAGE)
            return None

        host: str = str(config.get("host", "127.0.0.1"))
        port: int = int(config.get("port", 5672))
        username: str = str(config.get("username", "guest"))
        password: str = str(config.get("password", "guest"))
        vhost: str = str(config.get("vhost", "/"))

        return f"amqp://{username}:{password}@{host}:{port}/{vhost.lstrip('/')}"

    async def connect(self) -> bool:
        """初始化连接，RobustConnection 后续自动处理重连"""
        if self.connection and not self.connection.is_closed:
            return True

        url: Optional[str] = self._build_url()
        if not url:
            return False

        try:
            # connect_robust 返回 RobustConnection，具备自动重连能力
            self.connection = await aio_pika.connect_robust(
                url,
                heartbeat=60,
                connection_attempts=3,
                retry_delay=1.0,
                timeout=10,
            )
            self.channel = await self.connection.channel()

            # 注册重连回调：重连后自动重新获取 channel
            self.connection.reconnect_callbacks.add(self._on_reconnect)

            Logger.info("RabbitMQ 连接成功（自动重连已启用）")
            return True
        except Exception as e:
            Logger.warning(f"RabbitMQ 连接失败: {e}")
            return False

    async def _on_reconnect(self, _: Any) -> None:
        """重连后的回调：重新获取 channel"""
        try:
            self.channel = await self.connection.channel()
            Logger.info("RabbitMQ 重连成功，channel 已恢复")
        except Exception as e:
            Logger.warning(f"RabbitMQ 重连后恢复 channel 失败: {e}")

    async def send_message_async(
        self, queue_name: str, message: Any, persistent: bool = True
    ) -> bool:
        """异步发送消息到队列

        依赖 RobustConnection 自动处理断连恢复，此处只做发送和错误记录。
        """
        try:
            if (
                self.channel is None
                or self.connection is None
                or self.connection.is_closed
            ):
                Logger.warning(Messages.RABBITMQ_NOT_CONNECTED_MESSAGE)
                return False

            # 声明队列（幂等操作），确保重连后队列存在
            await self.channel.declare_queue(queue_name, durable=True)

            # 序列化消息
            if isinstance(message, dict):
                message_body: str = json.dumps(message, ensure_ascii=False)
            else:
                message_body: str = str(message)

            delivery_mode: aio_pika.DeliveryMode = (
                aio_pika.DeliveryMode.PERSISTENT
                if persistent
                else aio_pika.DeliveryMode.NOT_PERSISTENT
            )

            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=message_body.encode("utf-8"),
                    delivery_mode=delivery_mode,
                    content_type="application/json",
                ),
                routing_key=queue_name,
            )

            Logger.info(f"消息已发送到队列 [{queue_name}]: {message_body[:100]}...")
            return True

        except Exception as e:
            Logger.warning(f"发送消息到队列 [{queue_name}] 失败: {e}")
            return False

    async def close_async(self) -> None:
        """关闭连接"""
        try:
            if self.channel and not self.channel.is_closed:
                await self.channel.close()
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
        except Exception as e:
            Logger.error(f"关闭 RabbitMQ 连接失败: {e}")
        finally:
            self.channel = None
            self.connection = None

    def close(self) -> None:
        """同步关闭连接（由 __del__ 调用）"""
        try:
            loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
            if loop.is_running():
                Logger.warning(Messages.AIO_PKA_EVENT_LOOP_ERROR)
                return
        except RuntimeError:
            pass
        try:
            asyncio.run(self.close_async())
        except Exception:
            pass

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
    """异步发送消息到队列"""
    try:
        client: Optional[RabbitMQClient] = get_rabbitmq_client()
        if client is None:
            Logger.warning(Messages.RABBITMQ_CLIENT_NOT_INITIALIZED_MESSAGE)
            return False
        return await client.send_message_async(queue_name, message, persistent)
    except Exception as e:
        Logger.error(f"发送消息失败: {e}")
        return False
