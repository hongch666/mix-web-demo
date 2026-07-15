import time
from typing import Any, Dict, Optional

import httpx
from app.common.middleware import get_current_user_id, get_current_username
from app.core.auth import InternalTokenUtil
from app.core.base import Logger
from app.core.client.nacos import get_service_instance
from app.core.config import load_config
from app.core.constants import HttpCode, Messages
from app.core.errors import BusinessException
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

# 共享 httpx 客户端实例（由 lifespan 初始化，复用连接池降低延迟）
_shared_http_client: Optional[httpx.AsyncClient] = None


def set_shared_http_client(client: httpx.AsyncClient) -> None:
    """由 lifespan 设置共享的 httpx 客户端"""
    global _shared_http_client
    _shared_http_client = client


def get_shared_http_client() -> Optional[httpx.AsyncClient]:
    """获取共享的 httpx 客户端"""
    return _shared_http_client


class CircuitBreakerOpenError(Exception):
    """熔断器处于打开状态"""


class SimpleCircuitBreaker:
    """轻量级熔断器，避免下游持续故障时请求雪崩"""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 15.0,
    ) -> None:
        self.failure_threshold: int = failure_threshold
        self.recovery_timeout: float = recovery_timeout
        self.failure_count: int = 0
        self.open_until: float = 0.0

    def allow_request(self) -> None:
        now: float = time.monotonic()
        if self.open_until > now:
            raise CircuitBreakerOpenError(Messages.CIRCUIT_BREAKER_OPEN)

    def record_success(self) -> None:
        self.failure_count = 0
        self.open_until = 0.0

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.open_until = time.monotonic() + self.recovery_timeout


_SERVICE_BREAKERS: Dict[str, SimpleCircuitBreaker] = {}


def _get_service_breaker(service_name: str) -> SimpleCircuitBreaker:
    breaker: Optional[SimpleCircuitBreaker] = _SERVICE_BREAKERS.get(service_name)
    if breaker is None:
        breaker = SimpleCircuitBreaker()
        _SERVICE_BREAKERS[service_name] = breaker
    return breaker


def _build_default_headers() -> Dict[str, str]:
    """构建基础用户上下文请求头"""
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    return {
        "X-User-Id": user_id,
        "X-Username": username,
    }


def _build_internal_token_header(user_id: str) -> Dict[str, str]:
    """构建内部服务令牌请求头"""
    try:
        internal_token_util: InternalTokenUtil = InternalTokenUtil()
        user_id_num: int = int(user_id) if user_id else -1
        final_user_id: int = user_id_num if user_id_num > 0 else -1
        service_config: Dict[str, Any] = load_config("nacos")
        service_name_config: str = service_config.get("service_name", "fastapi")
        internal_token: str = internal_token_util.generate_internal_token(
            final_user_id, service_name_config
        )
        return {"X-Internal-Token": f"Bearer {internal_token}"}
    except Exception as e:
        Logger.error(f"生成内部令牌失败: {str(e)}")
        return {}


def _merge_headers(headers: Optional[Dict[str, str]]) -> Dict[str, str]:
    """合并默认请求头与调用方自定义请求头"""
    default_headers: Dict[str, str] = _build_default_headers()
    default_headers.update(_build_internal_token_header(default_headers["X-User-Id"]))
    merged_headers: Dict[str, str] = {**default_headers, **(headers or {})}
    return merged_headers


def _resolve_service_url(service_name: str, path: str) -> str:
    """通过服务发现生成远程调用 URL"""
    instance: Dict[str, Any] = get_service_instance(service_name)
    return f"http://{instance['ip']}:{instance['port']}{path}"


def _should_retry_remote_call(error: Exception) -> bool:
    """仅对瞬时性错误重试，避免无意义放大故障"""
    if isinstance(error, httpx.RequestError):
        return True
    if isinstance(error, httpx.HTTPStatusError):
        return (
            error.response.status_code >= HttpCode.INTERNAL_SERVER_ERROR
            or error.response.status_code == HttpCode.TOO_MANY_REQUESTS
        )
    return False


def _before_retry_log(retry_state: RetryCallState) -> None:
    """输出 tenacity 重试日志"""
    error: Optional[BaseException] = retry_state.outcome.exception()
    Logger.warning(
        f"调用远程服务失败，准备第 {retry_state.attempt_number + 1} 次重试: {error}"
    )


async def _request_remote_service(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]],
    data: Optional[Dict[str, Any]],
    json: Optional[Dict[str, Any]],
) -> Any:
    """执行一次真正的异步远程请求"""
    response: httpx.Response = await client.request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        data=data,
        json=json,
    )
    response.raise_for_status()
    return response.json()


def _build_remote_service_error(
    service_name: str, error: Exception
) -> BusinessException:
    """统一映射远程调用错误"""
    if isinstance(error, CircuitBreakerOpenError):
        Logger.warning(f"调用 {service_name} 已触发熔断，直接降级返回")
        return BusinessException(
            f"调用远程服务 {service_name} 已降级，请稍后再试",
            HttpCode.SERVICE_UNAVAILABLE,
            "SERVICE_CALL_FAILED",
        )
    if isinstance(error, httpx.HTTPStatusError):
        status_code: int = error.response.status_code
        Logger.error(
            f"调用 {service_name} 返回非 2xx 状态码: {status_code}, url={error.request.url}"
        )
    elif isinstance(error, httpx.RequestError):
        Logger.error(f"调用 {service_name} 网络异常: {error}")
    elif isinstance(error, ValueError):
        Logger.error(f"调用 {service_name} 响应解析失败: {error}")
    else:
        Logger.error(f"调用 {service_name} 失败: {error}")

    return BusinessException(
        f"调用远程服务 {service_name} 失败，请稍后重试",
        HttpCode.BAD_GATEWAY,
        Messages.ERROR_SERVICE_CALL_FAILED,
    )


async def call_remote_service(
    service_name: str,
    path: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    retries: int = 3,
    timeout: int = 5,
) -> Any:
    """
    通过 Nacos 服务发现并调用远程服务

    优先使用 lifespan 中创建的共享 httpx.AsyncClient（长连接池复用），
    不可用时才创建临时客户端。
    """
    merged_headers: Dict[str, str] = _merge_headers(headers)
    breaker: SimpleCircuitBreaker = _get_service_breaker(service_name)

    # 优先使用共享长连接池，不可用时创建临时客户端
    shared_client: Optional[httpx.AsyncClient] = get_shared_http_client()
    if shared_client is not None:
        return await _call_with_client(
            shared_client,
            service_name,
            path,
            method,
            merged_headers,
            params,
            data,
            json,
            retries,
            breaker,
            timeout,
        )
    else:
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await _call_with_client(
                client,
                service_name,
                path,
                method,
                merged_headers,
                params,
                data,
                json,
                retries,
                breaker,
                timeout,
            )


async def _call_with_client(
    client: httpx.AsyncClient,
    service_name: str,
    path: str,
    method: str,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]],
    data: Optional[Dict[str, Any]],
    json: Optional[Dict[str, Any]],
    retries: int,
    breaker: SimpleCircuitBreaker,
    timeout: int,
) -> Any:
    """使用指定客户端执行远程调用（含熔断和重试）"""
    try:
        breaker.allow_request()
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(retries),
            wait=wait_exponential(multiplier=0.2, min=0.2, max=2),
            retry=retry_if_exception(_should_retry_remote_call),
            before_sleep=_before_retry_log,
            reraise=True,
        ):
            with attempt:
                url: str = _resolve_service_url(service_name, path)
                Logger.info(
                    f"正在调用 {service_name} 的接口：{method} {url}（第 {attempt.retry_state.attempt_number} 次尝试）"
                )
                result: Any = await _request_remote_service(
                    client=client,
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json,
                )
                # 校验业务响应码
                if isinstance(result, dict) and result.get("code") != HttpCode.OK:
                    error_msg: str = result.get("msg", Messages.UNKNOWN_ERROR)
                    Logger.error(
                        f"服务 {service_name} 返回业务错误: code={result.get('code')}, msg={error_msg}"
                    )
                    raise BusinessException(
                        f"调用远程服务 {service_name} 失败: {error_msg}",
                        HttpCode.BAD_GATEWAY,
                        Messages.ERROR_SERVICE_CALL_FAILED,
                    )
                breaker.record_success()
                return result
    except Exception as e:
        if not isinstance(e, CircuitBreakerOpenError):
            breaker.record_failure()
        raise _build_remote_service_error(service_name, e)

    raise BusinessException(
        f"调用远程服务 {service_name} 失败，请稍后重试",
        HttpCode.BAD_GATEWAY,
        Messages.ERROR_SERVICE_CALL_FAILED,
    )
