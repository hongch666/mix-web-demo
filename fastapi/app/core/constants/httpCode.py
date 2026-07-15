class HttpCode:
    """HTTP 状态码常量 - 与 HTTP 响应状态码一致，同时作为响应体中的 code 字段值"""

    OK: int = 200
    BAD_REQUEST: int = 400
    UNAUTHORIZED: int = 401
    FORBIDDEN: int = 403
    NOT_FOUND: int = 404
    CONFLICT: int = 409
    UNPROCESSABLE_ENTITY: int = 422
    TOO_MANY_REQUESTS: int = 429
    INTERNAL_SERVER_ERROR: int = 500
    BAD_GATEWAY: int = 502
    SERVICE_UNAVAILABLE: int = 503
    GATEWAY_TIMEOUT: int = 504
