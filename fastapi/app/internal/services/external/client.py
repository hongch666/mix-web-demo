import asyncio
from typing import Any, Dict, Optional

import httpx
from app.common.middleware import get_current_user_id, get_current_username
from app.core.auth import InternalTokenUtil
from app.core.base import Logger
from app.core.config import load_config
from app.core.db import get_service_instance
from app.core.errors import BusinessException


def _build_default_headers() -> Dict[str, str]:
    """构建基础用户上下文请求头。"""
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    return {
        "X-User-Id": user_id,
        "X-Username": username,
    }


def _build_internal_token_header(user_id: str) -> Dict[str, str]:
    """构建内部服务令牌请求头。"""
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
    """合并默认请求头与调用方自定义请求头。"""
    default_headers: Dict[str, str] = _build_default_headers()
    default_headers.update(_build_internal_token_header(default_headers["X-User-Id"]))
    merged_headers: Dict[str, str] = {**default_headers, **(headers or {})}
    return merged_headers


def _resolve_service_url(service_name: str, path: str) -> str:
    """通过服务发现生成远程调用 URL。"""
    instance: Dict[str, Any] = get_service_instance(service_name)
    return f"http://{instance['ip']}:{instance['port']}{path}"


async def _request_remote_service(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]],
    data: Optional[Dict[str, Any]],
    json: Optional[Dict[str, Any]],
) -> Any:
    """执行一次真正的异步远程请求。"""
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


def _build_remote_service_error(service_name: str, error: Exception) -> BusinessException:
    """统一映射远程调用错误。"""
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

    return BusinessException(f"调用远程服务 {service_name} 失败，请稍后重试")


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
    """
    merged_headers: Dict[str, str] = _merge_headers(headers)
    retry_delay_seconds: float = 0.2

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(retries):
            try:
                url: str = _resolve_service_url(service_name, path)
                Logger.info(
                    f"正在调用 {service_name} 的接口：{method} {url}（第 {attempt + 1} 次尝试）"
                )
                return await _request_remote_service(
                    client=client,
                    method=method,
                    url=url,
                    headers=merged_headers,
                    params=params,
                    data=data,
                    json=json,
                )
            except Exception as e:
                if attempt < retries - 1:
                    Logger.warning(
                        f"调用 {service_name} 失败，第 {attempt + 1}/{retries} 次重试: {e}"
                    )
                    await asyncio.sleep(min(retry_delay_seconds * (2**attempt), 2.0))
                    continue

                raise _build_remote_service_error(service_name, e)

    raise BusinessException(f"调用远程服务 {service_name} 失败，请稍后重试")
