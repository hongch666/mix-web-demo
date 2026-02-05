import json
import pika
from typing import Any, Optional
from config.config import load_config
from common.utils import fileLogger as logger, Constants

class RabbitMQClient:
    """RabbitMQ 客户端"""

    def __init__(self):
        """初始化 RabbitMQ 客户端"""
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self._is_connected = False
        # 初始化时创建使用的队列
        self._create_queues()

    def _connect(self):
        """建立 RabbitMQ 连接"""
        if self._is_connected:
            return
            
        try:
            # 从配置文件获取连接参数
            rabbitmq_config = load_config("rabbitmq")
            if not rabbitmq_config:
                logger.warning(Constants.RABBITMQ_CONFIG_NOT_FOUND_MESSAGE)
                return
                
            host = str(rabbitmq_config.get("host", "127.0.0.1"))
            port = int(rabbitmq_config.get("port", 5672))
            username = str(rabbitmq_config.get("username", "guest"))
            password = str(rabbitmq_config.get("password", "guest"))
            vhost = str(rabbitmq_config.get("vhost", "/"))

            # 创建连接参数
            credentials = pika.PlainCredentials(username, password)
            parameters = pika.ConnectionParameters(
                host=host,
                port=port,
                virtual_host=vhost,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )

            # 建立连接
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self._is_connected = True

            logger.info(f"RabbitMQ 连接成功: {host}:{port}")

        except Exception as e:
            self._is_connected = False
            logger.warning(f"RabbitMQ 连接失败: {e}")
            # 不抛出异常，允许应用继续运行

    def send_message(self, queue_name: str, message: Any, persistent: bool = True) -> bool:
        """
        发送消息到指定队列

        Args:
            queue_name: 队列名称
            message: 消息内容（字典或字符串）
            persistent: 是否持久化消息

        Returns:
            bool: 发送是否成功
        """
        try:
            # 如果还没连接，先连接
            if not self._is_connected:
                self._connect()
            
            # 如果连接失败，返回 False
            if not self._is_connected or self.channel is None:
                logger.error(Constants.RABBITMQ_NOT_CONNECTED_MESSAGE)
                return False

            # 如果连接已关闭，重新连接
            if self.connection is None or self.connection.is_closed:
                self._is_connected = False
                self._connect()
                
            if not self._is_connected or self.channel is None:
                return False

            # 声明队列（幂等操作）
            self.channel.queue_declare(
                queue=queue_name,
                durable=True,  # 队列持久化
                exclusive=False,
                auto_delete=False,
            )

            # 序列化消息
            if isinstance(message, dict):
                message_body = json.dumps(message, ensure_ascii=False)
            else:
                message_body = str(message)

            # 发送消息
            delivery_mode = 2 if persistent else 1  # 2 = persistent
            self.channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=message_body.encode("utf-8"),
                properties=pika.BasicProperties(
                    delivery_mode=delivery_mode,
                    content_type="application/json",
                ),
            )

            logger.info(f"消息已发送到队列 [{queue_name}]: {message_body[:100]}...")
            return True

        except Exception as e:
            logger.error(f"发送消息到队列 [{queue_name}] 失败: {e}")
            self._is_connected = False
            return False

    def close(self):
        """关闭连接"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            self._is_connected = False
            logger.info(Constants.RABBITMQ_CONNECTION_CLOSED_MESSAGE)
        except Exception as e:
            logger.error(f"关闭 RabbitMQ 连接失败: {e}")

    def _create_queues(self):
        """在初始化时创建所有使用的队列"""
        try:
            # 先建立连接
            if not self._is_connected:
                self._connect()

            if not self._is_connected or self.channel is None:
                logger.warning(Constants.RABBITMQ_CREATE_QUEUES_FAILURE_MESSAGE)
                return

            # 定义使用的队列列表
            queues = [
                "api-log-queue",  # API日志队列，由apiLog装饰器使用
            ]

            # 声明队列
            for queue_name in queues:
                try:
                    self.channel.queue_declare(
                        queue=queue_name,
                        durable=True,  # 队列持久化
                        exclusive=False,
                        auto_delete=False,
                    )
                    logger.info(f"队列 [{queue_name}] 创建成功")
                except Exception as e:
                    logger.error(f"创建队列 [{queue_name}] 失败: {e}")

        except Exception as e:
            logger.error(f"创建队列时发生错误: {e}")

    def __del__(self):
        """析构函数，确保连接关闭"""
        self.close()


# 全局 RabbitMQ 客户端实例
_rabbitmq_client: Optional[RabbitMQClient] = None


def get_rabbitmq_client() -> Optional[RabbitMQClient]:
    """
    获取全局 RabbitMQ 客户端实例（单例模式）

    Returns:
        RabbitMQClient: RabbitMQ 客户端实例，如果初始化失败则返回 None
    """
    global _rabbitmq_client
    if _rabbitmq_client is None:
        try:
            _rabbitmq_client = RabbitMQClient()
        except Exception as e:
            logger.error(f"初始化 RabbitMQ 客户端失败: {e}")
            return None
    return _rabbitmq_client


def send_to_queue(queue_name: str, message: Any, persistent: bool = True) -> bool:
    """
    便捷函数：发送消息到队列

    Args:
        queue_name: 队列名称
        message: 消息内容
        persistent: 是否持久化

    Returns:
        bool: 发送是否成功
    """
    try:
        client = get_rabbitmq_client()
        if client is None:
            logger.warning(Constants.RABBITMQ_CLIENT_NOT_INITIALIZED_MESSAGE)
            return False
        return client.send_message(queue_name, message, persistent)
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return False
