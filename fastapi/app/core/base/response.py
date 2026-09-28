from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel, Field

from app.core.constants import HttpCode

T = TypeVar("T")


class ApiResponse[T](BaseModel):
    """统一响应模型，data 的结构由泛型参数声明"""

    code: int = Field(description="响应码")
    data: T | None = Field(default=None, description="返回数据")
    msg: str = Field(default="success", description="响应消息")


def success[T](data: T | None = None, msg: str = "success") -> ApiResponse[T]:
    """返回成功响应"""

    return ApiResponse[T](code=HttpCode.OK, data=data, msg=msg)


def error(
    code: int = HttpCode.INTERNAL_SERVER_ERROR,
    msg: str = "error",
    data: object | None = None,
) -> ApiResponse[object]:
    """返回错误响应"""

    return ApiResponse[object](code=code, data=data, msg=msg)
