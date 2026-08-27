"""测试全局配置，统一管理单例缓存的重置逻辑。"""

import inspect
from typing import Generator

import pytest

import app.internal.services as services_module


@pytest.fixture(autouse=True)
def clear_service_caches() -> Generator[None, None, None]:
    """每个测试执行前后清空所有 lru_cache 服务工厂的单例缓存。

    自动扫描 services 包导出的成员，凡带有 cache_clear 属性的
    工厂函数一律重置，避免测试之间共享带状态的缓存实例。
    """
    for name in dir(services_module):
        if name.startswith("_"):
            continue
        member = getattr(services_module, name)
        if inspect.isfunction(member) and hasattr(member, "cache_clear"):
            member.cache_clear()
    yield
    for name in dir(services_module):
        if name.startswith("_"):
            continue
        member = getattr(services_module, name)
        if inspect.isfunction(member) and hasattr(member, "cache_clear"):
            member.cache_clear()
