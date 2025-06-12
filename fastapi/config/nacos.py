import threading
import time
import nacos
import socket

from config.config import load_config

# Nacos 配置
nacos_config = load_config("nacos")

SERVER_ADDRESSES = nacos_config["server_addresses"]
NAMESPACE = nacos_config["namespace"]
SERVICE_NAME = nacos_config["service_name"]
GROUP_NAME = nacos_config["group_name"]

server_config = load_config("server")
IP = server_config["ip"]
PORT = server_config["port"]

client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE)

def register_instance(ip=IP, port=PORT):
    if not ip:
        ip = socket.gethostbyname(socket.gethostname())
    client.add_naming_instance(SERVICE_NAME, ip, port, group_name=GROUP_NAME)

def get_service_instance(service_name):
    instances = client.list_naming_instance(service_name, group_name=GROUP_NAME)
    # 简单负载均衡：随机选一个
    import random
    hosts = instances.get("hosts", [])
    if not hosts:
        raise Exception("No instance found")
    return random.choice(hosts)

def start_nacos(ip="127.0.0.1", port=8084):
    register_instance(ip=ip, port=port)
    def keep_heartbeat():
        while True:
            try:
                client.send_heartbeat(SERVICE_NAME, ip, port, group_name=GROUP_NAME)
            except Exception as e:
                print("Nacos heartbeat error:", e)
            time.sleep(10)
    threading.Thread(target=keep_heartbeat, daemon=True).start()