"""
启动/初始化消息类 — DeepSeek/Gemini/GPT 初始化日志
"""


class InitMessages:
    DEEPSEEK_INIT_LOG: str = "DeepSeek 客户端初始化完成"
    GEMINI_INIT_LOG: str = "Gemini 客户端初始化完成"
    GPT_INIT_LOG: str = "GPT 客户端初始化完成"
    STARTUP_MESSAGE: str = "FastAPI服务启动成功"
    INIT_IP: str = "127.0.0.1"
    HTTP_CLIENT_POOL_INITIALIZED: str = "HTTP 客户端连接池已创建"
    HTTP_CLIENT_POOL_CLOSED: str = "HTTP 客户端连接池已关闭"
    SCHEDULER_STARTED: str = "定时任务调度器已启动"
