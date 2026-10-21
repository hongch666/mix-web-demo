from typing import Any

from pydantic import Field


def to_snake(camel_name: str) -> str:
    """把驼峰命名的字段名转换为蛇形命名"""
    return "".join(
        f"_{char.lower()}" if char.isupper() else char for char in camel_name
    ).lstrip("_")


def Alias(camel_name: str, **kwargs: Any) -> Any:
    """构建同时设置校验与序列化别名的字段，兼容前端驼峰与后端蛇形命名"""
    snake_name = to_snake(camel_name)
    return Field(
        validation_alias=snake_name,
        serialization_alias=snake_name,
        **kwargs,
    )
