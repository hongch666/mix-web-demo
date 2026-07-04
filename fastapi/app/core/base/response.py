from typing import Any, Optional

from pydantic import BaseModel

from .httpCode import HttpCode


class ApiResponse(BaseModel):
    """统一响应模型

    Attributes:
        code: 响应码, 与 HTTP 状态码一致
        data: 返回数据, 默认为 None
        msg: 响应消息
    """

    code: int
    data: Optional[Any] = None
    msg: str = "success"


def success(data: Optional[Any] = None, msg: str = "success") -> ApiResponse:
    """返回成功响应

    Args:
        data: 返回数据, 默认为 None
        msg: 返回消息, 默认为 'success'

    Returns:
        ApiResponse 实例, code 为 200
    """
    return ApiResponse(code=HttpCode.OK, data=data, msg=msg)


def error(
    code: int = HttpCode.INTERNAL_SERVER_ERROR,
    msg: str = "error",
    data: Optional[Any] = None,
) -> ApiResponse:
    """返回错误响应

    Args:
        code: 3 位 HTTP 状态码, 默认为 500
        msg: 错误消息, 默认为 'error'
        data: 附加数据, 默认为 None

    Returns:
        ApiResponse 实例
    """
    return ApiResponse(code=code, data=data, msg=msg)
