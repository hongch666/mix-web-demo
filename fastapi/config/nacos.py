import threading
import time
import nacos
import socket

# Nacos 配置
SERVER_ADDRESSES = "127.0.0.1:8848"
NAMESPACE = "public"
SERVICE_NAME = "fastapi"
GROUP_NAME = "DEFAULT_GROUP"

client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE)

def register_instance(ip="127.0.0.1", port=8084):
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