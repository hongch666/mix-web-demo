import inspect
import json
import time
from functools import wraps
from typing import Any, Callable, List, Optional, Union
from fastapi import Request
from common.middleware import get_current_user_id, get_current_username
from common.utils import fileLogger
from config import send_to_queue

try:
    RABBITMQ_AVAILABLE = True
except ImportError:
    RABBITMQ_AVAILABLE = False
    fileLogger.warning("RabbitMQ 客户端不可用，API 日志将不会发送到队列")


class ApiLogConfig:
    """API 日志配置类"""
    
    def __init__(
        self,
        message: str,
        include_params: bool = True,
        log_level: str = "info",
        exclude_fields: Optional[List[str]] = None
    ):
        self.message = message
        self.include_params = include_params
        self.log_level = log_level
        self.exclude_fields = exclude_fields or []


def api_log(config: Union[str, ApiLogConfig]):
    """
    API 日志装饰器
    
    Args:
        config: 日志配置，可以是字符串（消息）或 ApiLogConfig 对象
        
    Examples:
        @api_log("获取前10篇文章")
        async def get_top10_articles():
            pass
            
        @api_log(ApiLogConfig("生成词云图", include_params=False))
        async def get_wordcloud():
            pass
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 处理配置
            if isinstance(config, str):
                log_config = ApiLogConfig(config)
            else:
                log_config = config
                
            # 获取用户信息
            user_id = get_current_user_id() or ""
            username = get_current_username() or ""
            
            # 从参数中获取 Request 对象
            request = _get_request_from_args(args, kwargs)
            
            if request:
                method = request.method
                path = request.url.path
            else:
                # 如果没有 Request 对象，使用默认值
                method = "UNKNOWN"
                path = f"/{func.__name__}"
            
            # 构建基础日志消息
            log_message = f"用户{user_id}:{username} {method} {path}: {log_config.message}"
            
            # 添加参数信息
            if log_config.include_params:
                params_info = _extract_params_info(func, args, kwargs, log_config.exclude_fields)
                if params_info:
                    log_message += f"\n{params_info}"
            
            # 记录日志
            logger_method = getattr(fileLogger, log_config.log_level, fileLogger.info)
            logger_method(log_message)

            # 执行原函数并记录耗时
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration_ms = int((time.time() - start) * 1000)
                time_message = f"{method} {path} 使用了{duration_ms}ms"
                logger_method(time_message)
                
                # 🚀 发送 API 日志到 RabbitMQ
                _send_api_log_to_queue(
                    user_id, username, method, path, log_config.message,
                    request, duration_ms, log_config
                )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 处理配置
            if isinstance(config, str):
                log_config = ApiLogConfig(config)
            else:
                log_config = config
                
            # 获取用户信息
            user_id = get_current_user_id() or ""
            username = get_current_username() or ""
            
            # 从参数中获取 Request 对象
            request = _get_request_from_args(args, kwargs)
            
            if request:
                method = request.method
                path = request.url.path
            else:
                # 如果没有 Request 对象，使用默认值
                method = "UNKNOWN"
                path = f"/{func.__name__}"
            
            # 构建基础日志消息
            log_message = f"用户{user_id}:{username} {method} {path}: {log_config.message}"
            
            # 添加参数信息
            if log_config.include_params:
                params_info = _extract_params_info(func, args, kwargs, log_config.exclude_fields)
                if params_info:
                    log_message += f"\n{params_info}"
            
            # 记录日志
            logger_method = getattr(fileLogger, log_config.log_level, fileLogger.info)
            logger_method(log_message)

            # 执行原函数并记录耗时
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = int((time.time() - start) * 1000)
                time_message = f"{method} {path} 使用了{duration_ms}ms"
                logger_method(time_message)
                
                # 🚀 发送 API 日志到 RabbitMQ
                _send_api_log_to_queue(
                    user_id, username, method, path, log_config.message,
                    request, duration_ms, log_config
                )
        
        # 根据函数是否为协程选择包装器
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _get_request_from_args(args: tuple, kwargs: dict) -> Optional[Request]:
    """
    从函数参数中提取 Request 对象
    
    Args:
        args: 位置参数
        kwargs: 关键字参数
        
    Returns:
        Request 对象或 None
    """
    # 从位置参数中查找
    for arg in args:
        if isinstance(arg, Request):
            return arg
    
    # 从关键字参数中查找
    for value in kwargs.values():
        if isinstance(value, Request):
            return value
    
    return None


def _extract_params_info(func: Callable, args: tuple, kwargs: dict, exclude_fields: List[str]) -> str:
    """
    提取参数信息
    
    Args:
        func: 被装饰的函数
        args: 位置参数
        kwargs: 关键字参数
        exclude_fields: 需要排除的字段
        
    Returns:
        str: 格式化的参数信息
    """
    try:
        # 获取函数签名
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())
        
        # 过滤掉依赖注入的参数（如 db, service 等）
        filtered_params = {}
        dependency_types = ['Session', 'AnalyzeService', 'ArticleService']
        
        # 处理位置参数
        for i, arg in enumerate(args):
            if i < len(param_names):
                param_name = param_names[i]
                param_type = str(sig.parameters[param_name].annotation)
                
                # 跳过依赖注入参数
                if not any(dep_type in param_type for dep_type in dependency_types):
                    if param_name not in exclude_fields:
                        filtered_params[param_name] = _serialize_param(arg)
        
        # 处理关键字参数
        for key, value in kwargs.items():
            if key in param_names:
                param_type = str(sig.parameters[key].annotation)
                
                # 跳过依赖注入参数
                if not any(dep_type in param_type for dep_type in dependency_types):
                    if key not in exclude_fields:
                        filtered_params[key] = _serialize_param(value)
        
        # 格式化输出
        if filtered_params:
            param_info = []
            for key, value in filtered_params.items():
                param_info.append(f"{key}: {value}")
            return "\n".join(param_info)
        
        return ""
        
    except Exception as e:
        return f"参数解析失败: {str(e)}"


def _serialize_param(param: Any) -> str:
    """
    序列化参数值
    
    Args:
        param: 参数值
        
    Returns:
        str: 序列化后的字符串
    """
    try:
        if isinstance(param, (str, int, float, bool)):
            return str(param)
        elif isinstance(param, (list, dict)):
            return json.dumps(param, ensure_ascii=False, default=str)
        else:
            return str(param)
    except Exception:
        return str(type(param).__name__)


def _send_api_log_to_queue(
    user_id: Any,
    username: str,
    method: str,
    path: str,
    description: str,
    request: Optional[Request],
    response_time_ms: int,
    log_config: ApiLogConfig,
):
    """
    发送 API 日志到 RabbitMQ
    
    Args:
        user_id: 用户ID
        username: 用户名
        method: HTTP方法
        path: 请求路径
        description: API描述
        request: Request对象
        response_time_ms: 响应时间（毫秒）
        log_config: 日志配置
    """
    if not RABBITMQ_AVAILABLE:
        return
    
    try:
        # 提取查询参数
        query_params = None
        if request and request.query_params:
            query_params = dict(request.query_params)
        
        # 提取路径参数
        path_params = None
        if request and hasattr(request, "path_params") and request.path_params:
            path_params = dict(request.path_params)
        
        # 提取请求体（如果需要且可用）
        request_body = None
        if log_config.include_params and request:
            # 注意：在 FastAPI 中，请求体通常在路由函数参数中，
            # 这里我们无法直接获取。如果需要，可以从 args/kwargs 中提取
            pass
        
        # 确保 user_id 是数字类型，如果为空则使用默认值
        final_user_id = user_id if user_id else 0
        if isinstance(final_user_id, str):
            try:
                final_user_id = int(final_user_id)
            except (ValueError, TypeError):
                final_user_id = 0
        
        # 确保 username 不为空
        final_username = username if username else "匿名用户"
        
        # 构建 API 日志消息（统一格式：snake_case）
        api_log_message = {
            "user_id": final_user_id,
            "username": final_username,
            "api_description": description,
            "api_path": path,
            "api_method": method,
            "query_params": query_params,
            "path_params": path_params,
            "request_body": request_body,
            "response_time": response_time_ms,
        }
        
        # 发送到 RabbitMQ
        success = send_to_queue("api-log-queue", api_log_message, persistent=True)
        if success:
            fileLogger.info("API 日志已发送到队列")
        else:
            fileLogger.error("API 日志发送到队列失败")
            
    except Exception as e:
        fileLogger.error(f"发送 API 日志到队列时出错: {e}")


# 简化版装饰器，直接传入消息
def log(message: str):
    """
    简化版日志装饰器
    
    Args:
        message: 日志消息
        
    Example:
        @log("获取前10篇文章")
        async def get_top10_articles():
            pass
    """
    return api_log(message)


# 高级配置装饰器
def log_with_config(
    message: str,
    include_params: bool = True,
    log_level: str = "info",
    exclude_fields: Optional[List[str]] = None
):
    """
    带配置的日志装饰器
    
    Args:
        message: 日志消息
        include_params: 是否包含参数
        log_level: 日志级别
        exclude_fields: 排除的字段
        
    Example:
        @log_with_config("敏感操作", include_params=False, log_level="warn")
        async def sensitive_operation():
            pass
    """
    return api_log(ApiLogConfig(message, include_params, log_level, exclude_fields))