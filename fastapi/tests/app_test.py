"""应用启动冒烟测试

依赖装配错误（如 provide_* 中裸类型注解的 Depends 参数）只有在
路由注册构建依赖图时才会暴露，纯语法编译与函数级单测都无法发现，
此处通过完整导入并构建应用兜底
"""

from fastapi import FastAPI

from main import app


def test_app() -> None:
    """全量导入应用，确保所有路由的依赖图可以正常解析"""
    assert isinstance(app, FastAPI)
    assert len(app.routes) > 0
