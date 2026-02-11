import requests
from common.utils import fileLogger as logger
from typing import Optional, Dict, Any
from common.config import get_service_instance, load_config
from common.middleware import get_current_user_id, get_current_username
from common.exceptions import BusinessException
from common.utils import InternalTokenUtil

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

    # 生成并添加内部服务令牌 (没有用户ID时用-1代表系统调用)
    try:
        internal_token_util: InternalTokenUtil = InternalTokenUtil()
        user_id_num: int = int(user_id) if user_id else -1
        final_user_id: int = user_id_num if user_id_num > 0 else -1
        service_config: Dict[str, Any] = load_config("nacos")
        service_name_config: str = service_config.get("service_name", "fastapi")
        internal_token: str = internal_token_util.generate_internal_token(
            final_user_id, service_name_config
        )
        default_headers["X-Internal-Token"] = f"Bearer {internal_token}"
    except Exception as e:
        logger.error(f"生成内部令牌失败: {str(e)}")

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