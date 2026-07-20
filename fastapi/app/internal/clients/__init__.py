"""
内部服务调用客户端
按目标服务拆分，不按业务调用方拆分。
"""

from .nestjsClient import NestjsClient

__all__: list[str] = [
    "NestjsClient",
]
