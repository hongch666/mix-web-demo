import requests
from common.utils import fileLogger as logger
from typing import Optional, Dict, Any
from config import get_service_instance
from common.middleware import get_current_user_id, get_current_username
from common.exceptions import BusinessException

async def call_remote_service(
    service_name: str,
    path: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    retries: int = 3,
    timeout: int = 5
) -> Any:
    """
    通过 Nacos 服务发现并调用远程服务
    """
    # 默认请求头
    user_id: str = get_current_user_id() or ""
    username: str = get_current_username() or ""
    default_headers: Dict[str, str] = {
        "X-User-Id": user_id,
        "X-Username": username,
    }
    # 合并默认和自定义请求头
    merged_headers: Dict[str, str] = {**default_headers, **(headers or {})}

    for attempt in range(retries):
        try:
            instance: Dict[str, Any] = get_service_instance(service_name)
            url: str = f"http://{instance['ip']}:{instance['port']}{path}"
            logger.info(f"正在调用 {service_name} 的接口：{method} {url}（第 {attempt+1} 次尝试）")
            response: requests.Response = requests.request(
                method=method,
                url=url,
                headers=merged_headers,
                params=params,
                data=data,
                json=json,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"调用 {service_name} 失败: {e}")
            if attempt == retries - 1:
                raise BusinessException(f"调用远程服务 {service_name} 失败，请稍后重试")