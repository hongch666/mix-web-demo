"""
内部服务调用客户端
按目标服务拆分，不按业务调用方拆分。
"""

from .gozeroClient import GoZeroClient
from .nestjsClient import NestjsClient
from .springClient import SpringClient

__all__: list[str] = [
    "GoZeroClient",
    "NestjsClient",
    "SpringClient",
]
