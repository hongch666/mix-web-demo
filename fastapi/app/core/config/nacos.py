import random
import socket
import threading
import time
from typing import Any, Dict, List

import nacos
from app.core.base import Constants, Logger
from app.core.errors import BusinessException

from .config import load_config

# Nacos 配置
nacos_config: Dict[str, Any] = load_config("nacos")

SERVER_ADDRESSES: str = nacos_config["server_addresses"]
NAMESPACE: str = nacos_config["namespace"]
SERVICE_NAME: str = nacos_config["service_name"]
GROUP_NAME: str = nacos_config["group_name"]
USERNAME: str = nacos_config.get("username", "")
PASSWORD: str = nacos_config.get("password", "")
HEARTBEAT_INTERVAL: int = int(nacos_config.get("heartbeat_interval", 10))
REGISTER_RETRIES: int = int(nacos_config.get("register_retries", 5))
RETRY_INTERVAL: int = int(nacos_config.get("retry_interval", 2))

server_config: Dict[str, Any] = load_config("server")
IP: str = server_config["ip"]
PORT: int = server_config["port"]


def _build_client() -> nacos.NacosClient:
    kwargs: Dict[str, Any] = {"namespace": NAMESPACE}
    if USERNAME:
        kwargs["username"] = USERNAME
    if PASSWORD:
        kwargs["password"] = PASSWORD
    return nacos.NacosClient(SERVER_ADDRESSES, **kwargs)


client: nacos.NacosClient = _build_client()


def _get_registration_ip(ip: str) -> str:
    """
    获取用于 Nacos 注册的 IP 地址
    - 如果 ip 为空、127.0.0.1 或 0.0.0.0，获取真实 IP 地址
    - 否则自动解析真实 IP 地址
    """
    if not ip or ip == "127.0.0.1" or ip == "0.0.0.0":
        # 自动解析真实 IP
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            real_ip = sock.getsockname()[0]
            sock.close()
            Logger.info(f"自动解析本地 IP: {real_ip}")
            return real_ip
        except Exception as e:
            Logger.warning(f"自动解析 IP 失败: {e}，使用主机名")
            return socket.gethostbyname(socket.gethostname())

    return ip


def register_instance(ip: str = IP, port: int = PORT) -> None:
    # 获取实际用于注册的 IP 地址
    registration_ip = _get_registration_ip(ip)

    last_error: Exception | None = None
    for attempt in range(1, REGISTER_RETRIES + 1):
        try:
            client.add_naming_instance(
                SERVICE_NAME, registration_ip, port, group_name=GROUP_NAME
            )
            Logger.info(
                f"Nacos 注册成功: service={SERVICE_NAME}, address={registration_ip}:{port}, group={GROUP_NAME}"
            )
            return
        except Exception as e:
            last_error = e
            Logger.warning(
                f"Nacos 注册失败，第 {attempt}/{REGISTER_RETRIES} 次重试: {e}"
            )
            time.sleep(RETRY_INTERVAL)

    raise RuntimeError(
        f"Nacos 注册失败，已重试 {REGISTER_RETRIES} 次，server={SERVER_ADDRESSES}"
    ) from last_error


def get_service_instance(service_name: str) -> Dict[str, Any]:
    instances: Dict[str, Any] = client.list_naming_instance(
        service_name, group_name=GROUP_NAME
    )
    # 简单负载均衡：随机选一个
    hosts: List[Dict[str, Any]] = instances.get("hosts", [])
    if not hosts:
        raise BusinessException(Constants.AI_CHAT_NO_INSTANCE_MESSAGE)
    return random.choice(hosts)


def start_nacos(ip: str = "127.0.0.1", port: int = 8084) -> None:
    # 获取实际用于注册的 IP 地址
    registration_ip = _get_registration_ip(ip)
    register_instance(ip=registration_ip, port=port)

    def keep_heartbeat() -> None:
        while True:
            try:
                client.send_heartbeat(
                    SERVICE_NAME, registration_ip, port, group_name=GROUP_NAME
                )
            except Exception as e:
                Logger.error(f"Nacos 心跳错误: {e}")
            time.sleep(HEARTBEAT_INTERVAL)

    threading.Thread(target=keep_heartbeat, daemon=True).start()
