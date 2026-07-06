from .client import call_remote_service, get_shared_http_client, set_shared_http_client
from .nacos import get_service_instance, register_instance, start_nacos

__all__: list[str] = [
    "get_service_instance",
    "register_instance",
    "start_nacos",
    "call_remote_service",
    "set_shared_http_client",
    "get_shared_http_client",
]
