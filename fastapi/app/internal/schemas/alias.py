from typing import Any

from pydantic import Field


def to_snake(camel_name: str) -> str:
    return "".join(
        f"_{char.lower()}" if char.isupper() else char for char in camel_name
    ).lstrip("_")


def Alias(camel_name: str, **kwargs: Any) -> Any:
    snake_name = to_snake(camel_name)
    return Field(
        validation_alias=snake_name,
        serialization_alias=snake_name,
        **kwargs,
    )
