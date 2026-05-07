from .client import call_remote_service
from .nacos import get_service_instance, register_instance, start_nacos

__all__: list[str] = [
    "get_service_instance",
    "register_instance",
    "start_nacos",
    "call_remote_service",
]
