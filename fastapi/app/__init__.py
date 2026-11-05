from typing import Any

from fastapi import FastAPI


def create_app(*args: Any, **kwargs: Any) -> FastAPI:
    """延迟加载应用工厂，避免导入工具模块时初始化外部数据库驱动"""
    # lazy-import: import app 包时不引入遥测 SDK
    from app.core.telemetry import setup_telemetry

    setup_telemetry()
    # lazy-import: 只在真正创建应用时导入完整应用栈，避免导入工具模块即初始化数据库驱动
    from .app import create_app as _create_app

    return _create_app(*args, **kwargs)


__all__: list[str] = ["create_app"]
