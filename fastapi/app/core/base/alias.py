from typing import Any

from pydantic import Field


def to_snake(camel_name: str) -> str:
    """把驼峰命名的字段名转换为蛇形命名

    Args:
        camel_name: 驼峰形式的字段名

    Returns:
        str: 对应的蛇形字段名
    """
    return "".join(
        f"_{char.lower()}" if char.isupper() else char for char in camel_name
    ).lstrip("_")


def Alias(camel_name: str, **kwargs: Any) -> Any:
    """构建同时设置校验与序列化别名的字段，兼容前端驼峰与后端蛇形命名

    Args:
        camel_name: 前端驼峰字段名，后端统一按蛇形别名校验与序列化
        **kwargs: 透传给 pydantic.Field 的其余参数，如 default、description

    Returns:
        Any: 带蛇形校验别名与序列化别名的字段定义
    """
    snake_name = to_snake(camel_name)
    return Field(
        validation_alias=snake_name,
        serialization_alias=snake_name,
        **kwargs,
    )
