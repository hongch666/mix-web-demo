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
                result = await func(*args, **kwargs)
                
                # 如果返回的是 StreamingResponse，需要包装以追踪耗时
                from fastapi.responses import StreamingResponse
                if isinstance(result, StreamingResponse):
                    original_generator = result.body_iterator
                    
                    async def tracked_generator():
                        try:
                            async for chunk in original_generator:
                                yield chunk
                        finally:
                            # 流完成时记录耗时
                            duration_ms = int((time.time() - start) * 1000)
                            time_message = f"{method} {path} 使用了{duration_ms}ms"
                            logger_method(time_message)
                            
                            # 🚀 发送 API 日志到 RabbitMQ
                            _send_api_log_to_queue(
                                user_id, username, method, path, log_config.message,
                                request, duration_ms, log_config, args, kwargs
                            )
                    
                    result.body_iterator = tracked_generator()
                    return result
                else:
                    # 非流式响应，立即记录耗时
                    duration_ms = int((time.time() - start) * 1000)
                    time_message = f"{method} {path} 使用了{duration_ms}ms"
                    logger_method(time_message)
                    
                    # 🚀 发送 API 日志到 RabbitMQ
                    _send_api_log_to_queue(
                        user_id, username, method, path, log_config.message,
                        request, duration_ms, log_config, args, kwargs
                    )
                    return result
            except Exception as e:
                duration_ms = int((time.time() - start) * 1000)
                time_message = f"{method} {path} 使用了{duration_ms}ms (异常)"
                logger_method(time_message)
                raise

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
                    request, duration_ms, log_config, args, kwargs
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
        
        filtered_params = {}
        
        # 处理位置参数
        for i, arg in enumerate(args):
            if i < len(param_names):
                param_name = param_names[i]
                
                # 根据参数名称过滤依赖注入（数据库、HTTP 请求等）
                if param_name in {'db', 'session', 'httpRequest'}:
                    continue
                
                # 跳过 Service 类型的依赖注入（如 cozeService, geminiService）
                if 'Service' in param_name:
                    continue
                
                if param_name not in exclude_fields:
                    filtered_params[param_name] = _serialize_param(arg)
        
        # 处理关键字参数 - 这是FastAPI传入业务参数的主要方式
        for key, value in kwargs.items():
            if key in param_names:
                # 根据参数名称过滤依赖注入
                if key in {'db', 'session', 'httpRequest'}:
                    continue
                
                # 跳过 Service 类型的依赖注入 - 检查参数名称
                if 'Service' in key:
                    continue
                
                # 检查参数注解，排除纯 FastAPI Request 对象
                param_annotation = sig.parameters[key].annotation
                if param_annotation != inspect.Parameter.empty:
                    annotation_str = str(param_annotation)
                    # 排除 fastapi.Request 类型的参数，但保留其他包含 'Request' 的类型（如 ChatRequest）
                    if 'fastapi' in annotation_str and 'Request' in annotation_str:
                        continue
                    # 排除 sqlmodel.Session 等数据库相关
                    if any(db_type in annotation_str for db_type in ['Session', 'sqlmodel']):
                        continue
                
                # 跳过排除字段
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
            # 检查是否是 Pydantic 模型
            if hasattr(param, 'model_dump'):
                # Pydantic v2
                return json.dumps(param.model_dump(), ensure_ascii=False, default=str)
            elif hasattr(param, 'dict'):
                # Pydantic v1
                return json.dumps(param.dict(), ensure_ascii=False, default=str)
            else:
                # 其他对象转字符串
                return str(param)
    except Exception:
        return str(type(param).__name__)


def _extract_request_body_for_queue(kwargs: dict, exclude_fields: List[str]) -> Optional[dict]:
    """
    从函数参数中提取请求体信息用于发送到队列
    
    Args:
        kwargs: 函数关键字参数
        exclude_fields: 排除的字段
        
    Returns:
        dict: 请求体信息，如果没有则返回 None
    """
    try:
        request_body_dict = {}
        
        # 需要排除的参数名称（依赖注入）
        exclude_param_names = {'db', 'session', 'httpRequest'}
        
        for key, value in kwargs.items():
            # 跳过依赖注入参数
            if key in exclude_param_names:
                continue
            
            # 跳过 Service 类型参数
            if 'Service' in key:
                continue
            
            # 跳过用户排除的字段
            if key in exclude_fields:
                continue
            
            # 直接提取 Pydantic 模型的内容，不转为字符串
            if hasattr(value, 'model_dump'):
                # Pydantic v2
                request_body_dict.update(value.model_dump())
            elif hasattr(value, 'dict'):
                # Pydantic v1
                request_body_dict.update(value.dict())
            elif isinstance(value, dict):
                # 如果已经是字典，直接更新
                request_body_dict.update(value)
            else:
                # 其他类型保持原值
                request_body_dict[key] = value
        
        return request_body_dict if request_body_dict else None
        
    except Exception as e:
        fileLogger.warning(f"提取请求体信息时出错: {str(e)}")
        return None


def _send_api_log_to_queue(
    user_id: Any,
    username: str,
    method: str,
    path: str,
    description: str,
    request: Optional[Request],
    response_time_ms: int,
    log_config: ApiLogConfig,
    args: tuple = (),
    kwargs: dict = None,
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
        args: 函数位置参数
        kwargs: 函数关键字参数
    """
    if not RABBITMQ_AVAILABLE:
        return
    
    if kwargs is None:
        kwargs = {}
    
    try:
        # 提取查询参数
        query_params = None
        if request and request.query_params:
            query_params = dict(request.query_params)
        
        # 提取路径参数
        path_params = None
        if request and hasattr(request, "path_params") and request.path_params:
            path_params = dict(request.path_params)
        
        # 提取请求体 - 从参数中提取业务参数
        request_body = None
        if log_config.include_params:
            request_body = _extract_request_body_for_queue(kwargs, log_config.exclude_fields)
        
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