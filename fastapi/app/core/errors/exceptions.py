from app.core.constants import HttpCode


class BusinessException(Exception):
    """业务异常 - 用于返回可向客户端显示的错误信息

    Attributes:
        message: 返回给客户端的错误信息
        status_code: HTTP 状态码
        error: 错误标识，用于区分同一状态码下的不同错误场景
    """

    def __init__(
        self,
        message: str,
        status_code: int = HttpCode.BAD_REQUEST,
        error: str = "BUSINESS_ERROR",
    ) -> None:
        self.message: str = message
        self.status_code: int = status_code
        self.error: str = error
        super().__init__(self.message)

    def get_error_identifier(self) -> str:
        """获取错误标识"""
        return self.error

    # 便捷构造函数

    @staticmethod
    def bad_request(message: str, error: str = "BAD_REQUEST") -> "BusinessException":
        """创建 400 Bad Request 业务异常"""
        return BusinessException(message, HttpCode.BAD_REQUEST, error)

    @staticmethod
    def unauthorized(message: str, error: str = "UNAUTHORIZED") -> "BusinessException":
        """创建 401 Unauthorized 业务异常"""
        return BusinessException(message, HttpCode.UNAUTHORIZED, error)

    @staticmethod
    def forbidden(message: str, error: str = "FORBIDDEN") -> "BusinessException":
        """创建 403 Forbidden 业务异常"""
        return BusinessException(message, HttpCode.FORBIDDEN, error)

    @staticmethod
    def not_found(message: str, error: str = "NOT_FOUND") -> "BusinessException":
        """创建 404 Not Found 业务异常"""
        return BusinessException(message, HttpCode.NOT_FOUND, error)

    @staticmethod
    def conflict(message: str, error: str = "CONFLICT") -> "BusinessException":
        """创建 409 Conflict 业务异常"""
        return BusinessException(message, HttpCode.CONFLICT, error)

    @staticmethod
    def unprocessable_entity(
        message: str, error: str = "UNPROCESSABLE_ENTITY"
    ) -> "BusinessException":
        """创建 422 Unprocessable Entity 业务异常"""
        return BusinessException(message, HttpCode.UNPROCESSABLE_ENTITY, error)

    @staticmethod
    def too_many_requests(
        message: str, error: str = "TOO_MANY_REQUESTS"
    ) -> "BusinessException":
        """创建 429 Too Many Requests 业务异常"""
        return BusinessException(message, HttpCode.TOO_MANY_REQUESTS, error)

    @staticmethod
    def internal_server_error(
        message: str, error: str = "INTERNAL_SERVER_ERROR"
    ) -> "BusinessException":
        """创建 500 Internal Server Error 业务异常"""
        return BusinessException(message, HttpCode.INTERNAL_SERVER_ERROR, error)

    @staticmethod
    def bad_gateway(message: str, error: str = "BAD_GATEWAY") -> "BusinessException":
        """创建 502 Bad Gateway 业务异常"""
        return BusinessException(message, HttpCode.BAD_GATEWAY, error)

    @staticmethod
    def service_unavailable(
        message: str, error: str = "SERVICE_UNAVAILABLE"
    ) -> "BusinessException":
        """创建 503 Service Unavailable 业务异常"""
        return BusinessException(message, HttpCode.SERVICE_UNAVAILABLE, error)

    @staticmethod
    def gateway_timeout(
        message: str, error: str = "GATEWAY_TIMEOUT"
    ) -> "BusinessException":
        """创建 504 Gateway Timeout 业务异常"""
        return BusinessException(message, HttpCode.GATEWAY_TIMEOUT, error)
