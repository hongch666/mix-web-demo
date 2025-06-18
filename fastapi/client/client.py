import requests
import logging

from config.nacos import get_service_instance
from middleware.ContextMiddleware import get_current_user_id, get_current_username

async def call_remote_service(
    service_name: str,
    path: str,
    method: str = "GET",
    headers: dict = None,
    params: dict = None,
    data: dict = None,
    json: dict = None,
    retries: int = 3,
    timeout: int = 5
):
    """
    通过 Nacos 服务发现并调用远程服务
    """
    # 默认请求头
    user_id = get_current_user_id() or ""
    username = get_current_username() or ""
    default_headers = {
        "X-User-Id": user_id,
        "X-Username": username,
    }
    # 合并默认和自定义请求头
    merged_headers = {**default_headers, **(headers or {})}

    for attempt in range(retries):
        try:
            instance = get_service_instance(service_name)
            url = f"http://{instance['ip']}:{instance['port']}{path}"
            logging.info(f"Calling {method} {url} (attempt {attempt+1})")
            response = requests.request(
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
            logging.error(f"Error calling {service_name}: {e}")
            if attempt == retries - 1:
                raise