import functools
import inspect
import json
from typing import Any, Callable, List, Optional, Union
from common.middleware import get_current_user_id, get_current_username
from common.utils import fileLogger


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
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 处理配置
            if isinstance(config, str):
                log_config = ApiLogConfig(config)
            else:
                log_config = config
                
            # 获取用户信息
            user_id = get_current_user_id() or ""
            username = get_current_username() or ""
            
            # 获取请求信息
            method, path = _extract_request_info(func, args, kwargs)
            
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
            
            # 执行原函数
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 处理配置
            if isinstance(config, str):
                log_config = ApiLogConfig(config)
            else:
                log_config = config
                
            # 获取用户信息
            user_id = get_current_user_id() or ""
            username = get_current_username() or ""
            
            # 获取请求信息
            method, path = _extract_request_info(func, args, kwargs)
            
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
            
            # 执行原函数
            return func(*args, **kwargs)
        
        # 根据函数是否为协程选择包装器
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _extract_request_info(func: Callable, args: tuple, kwargs: dict) -> tuple[str, str]:
    """
    提取请求方法和路径信息
    
    Returns:
        tuple: (method, path)
    """
    # 尝试从函数名推断请求方法
    func_name = func.__name__
    
    if func_name.startswith('get_') or func_name.endswith('_list'):
        method = "GET"
    elif func_name.startswith('create_') or func_name.startswith('add_'):
        method = "POST"
    elif func_name.startswith('update_') or func_name.startswith('edit_'):
        method = "PUT"
    elif func_name.startswith('delete_') or func_name.startswith('remove_'):
        method = "DELETE"
    else:
        # 尝试从路由装饰器获取方法信息
        method = _get_method_from_router(func)
    
    # 尝试获取路径信息
    path = _get_path_from_router(func)
    
    return method, path


def _get_method_from_router(func: Callable) -> str:
    """从路由装饰器获取 HTTP 方法"""
    # 检查函数的路由装饰器信息
    if hasattr(func, '__route_methods__'):
        methods = getattr(func, '__route_methods__')
        if methods:
            return list(methods)[0].upper()
    
    # 默认返回 POST
    return "POST"


def _get_path_from_router(func: Callable) -> str:
    """从路由装饰器获取路径信息"""
    # 检查函数的路由装饰器信息
    if hasattr(func, '__route_path__'):
        return getattr(func, '__route_path__')
    
    # 根据函数名推断路径
    func_name = func.__name__
    
    # 常见的路径映射
    path_mappings = {
        'get_top10_articles': '/analyze/top10',
        'get_wordcloud': '/analyze/wordcloud',
        'get_excel': '/analyze/excel',
    }
    
    return path_mappings.get(func_name, f"/{func_name}")


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