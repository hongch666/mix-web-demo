import threading
import time
import nacos
import socket
from typing import Any, Dict

from config import load_config


def _get_logger():
    try:
        from common.utils import fileLogger as logger
        return logger
    except Exception:
        import logging
        return logging.getLogger('nacos')

# Nacos 配置
nacos_config: Dict[str, Any] = load_config("nacos")

SERVER_ADDRESSES: str = nacos_config["server_addresses"]
NAMESPACE: str = nacos_config["namespace"]
SERVICE_NAME: str = nacos_config["service_name"]
GROUP_NAME: str = nacos_config["group_name"]

server_config: Dict[str, Any] = load_config("server")
IP: str = server_config["ip"]
PORT: int = server_config["port"]

client: nacos.NacosClient = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE)

def register_instance(ip: str = IP, port: int = PORT) -> None:
    if not ip:
        ip = socket.gethostbyname(socket.gethostname())
    client.add_naming_instance(SERVICE_NAME, ip, port, group_name=GROUP_NAME)

def get_service_instance(service_name: str) -> dict:
    instances: dict = client.list_naming_instance(service_name, group_name=GROUP_NAME)
    # 简单负载均衡：随机选一个
    import random
    hosts: list = instances.get("hosts", [])
    if not hosts:
        raise Exception("No instance found")
    return random.choice(hosts)

def start_nacos(ip: str = "127.0.0.1", port: int = 8084) -> None:
    register_instance(ip=ip, port=port)
    def keep_heartbeat() -> None:
        while True:
            try:
                client.send_heartbeat(SERVICE_NAME, ip, port, group_name=GROUP_NAME)
            except Exception as e:
                _get_logger().error("Nacos heartbeat error: %s", e)
            time.sleep(10)
    threading.Thread(target=keep_heartbeat, daemon=True).start()