import inspect
import os
from collections.abc import Generator

import pytest


def _disable_langsmith_tracing() -> None:
    """单元测试强制关闭 LangSmith 追踪

    测试里的 FakeLLM 是 Runnable，链路会被 langsmith SDK 自动上报，
    若不关闭会把单测流量写进线上项目。必须在导入任何 app 模块之前执行：
    app.core.config 导入时会 load_dotenv()，而 dotenv 不覆盖已存在的环境变量，
    因此这里写入的关闭状态不会被 .env 里的配置覆盖
    """
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGSMITH_TRACING_V2"] = "false"
    for tracing_key in ("LANGCHAIN_TRACING", "LANGCHAIN_TRACING_V2"):
        os.environ.pop(tracing_key, None)

    try:
        from langsmith import configure as configure_langsmith
        from langsmith import utils as langsmith_utils
    except ImportError:
        return

    # 关闭全局追踪开关，覆盖环境变量与全局回退
    configure_langsmith(enabled=False)
    # 追踪开关与项目名读取带 lru_cache，清缓存避免复用进程内旧判定
    langsmith_utils.get_env_var.cache_clear()
    langsmith_utils.get_tracer_project.cache_clear()


_disable_langsmith_tracing()


@pytest.fixture(autouse=True)
def clear_service_caches() -> Generator[None, None, None]:
    """每个测试执行前后清空所有 lru_cache 服务工厂的单例缓存

    自动扫描 services 包导出的成员，凡带有 cache_clear 属性的工厂函数一律重置，避免测试之间共享带状态的缓存实例
    """
    try:
        import app.internal.services as services_module
    except Exception:
        services_module = None

    if services_module is not None:
        for name in dir(services_module):
            if name.startswith("_"):
                continue
            member = getattr(services_module, name)
            if inspect.isfunction(member) and hasattr(member, "cache_clear"):
                member.cache_clear()
    yield
    if services_module is not None:
        for name in dir(services_module):
            if name.startswith("_"):
                continue
            member = getattr(services_module, name)
            if inspect.isfunction(member) and hasattr(member, "cache_clear"):
                member.cache_clear()
