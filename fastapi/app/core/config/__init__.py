from typing import Any, List, NoReturn

from .config import load_config

try:
    from .nacos import get_service_instance, register_instance, start_nacos
except ModuleNotFoundError:

    def _missing_nacos(*args: Any, **kwargs: Any) -> NoReturn:
        raise ModuleNotFoundError("nacos 未安装，请先安装 nacos 依赖")

    get_service_instance = _missing_nacos
    register_instance = _missing_nacos
    start_nacos = _missing_nacos

__all__: List[str] = [
    "load_config",
    "get_service_instance",
    "register_instance",
    "start_nacos",
]
