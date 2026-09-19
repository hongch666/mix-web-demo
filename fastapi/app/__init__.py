def create_app(*args, **kwargs):
    """延迟加载应用工厂，避免导入工具模块时初始化外部数据库驱动。"""
    from app.core.telemetry import setup_telemetry

    setup_telemetry()
    from .app import create_app as _create_app

    return _create_app(*args, **kwargs)

__all__: list[str] = ["create_app"]
