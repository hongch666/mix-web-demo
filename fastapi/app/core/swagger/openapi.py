from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.core.constants import SwaggerConfig


def setup_openapi(app: FastAPI) -> None:
    """覆写应用的 openapi 方法，按项目声明生成并缓存 OpenAPI 文档

    FastAPI 默认按自身版本生成文档，这里改成 SwaggerConfig 声明的 OpenAPI 版本，
    并显式带上项目的 openapi_tags；结果写入 app.openapi_schema 后复用，避免每次请求重建

    Args:
        app: 待配置的 FastAPI 应用实例
    """

    def custom_openapi() -> dict[str, Any]:
        """命中缓存直接返回，否则按配置的版本、标题与标签重建并缓存"""
        if app.openapi_schema:
            return app.openapi_schema
        app.openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=SwaggerConfig.OPENAPI_VERSION,
            description=app.description,
            routes=app.routes,
            tags=SwaggerConfig.OPENAPI_TAGS,
        )
        return app.openapi_schema

    app.openapi = custom_openapi
