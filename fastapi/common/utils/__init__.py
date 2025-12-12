from .loggers import logger

from .response import success, fail

from .writeLog import write_log, log_info, log_error, log_warning, log_debug, SimpleLogger, fileLogger

from .baseAIService import BaseAiService, get_agent_prompt, initialize_ai_tools

__all__ = [
    "logger",
    "success",
    "fail",
    "write_log",
    "log_info",
    "log_error",
    "log_warning",
    "log_debug",
    "SimpleLogger",
    "fileLogger",
    "BaseAiService",
    "get_agent_prompt",
    "initialize_ai_tools",
    "BaseAiService",
    "get_agent_prompt",
    "initialize_ai_tools",
]

def __getattr__(name):
    """延迟导入 BaseAiService 相关的类和函数，避免循环导入"""
    if name == "BaseAiService":
        from .baseAIService import BaseAiService
        return BaseAiService
    elif name == "get_agent_prompt":
        from .baseAIService import get_agent_prompt
        return get_agent_prompt
    elif name == "initialize_ai_tools":
        from .baseAIService import initialize_ai_tools
        return initialize_ai_tools
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")