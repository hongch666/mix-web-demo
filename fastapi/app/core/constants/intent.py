from typing import Literal, get_args

# 意图类型：用户问题归属的处理领域
IntentType = Literal[
    "database_query",
    "article_search",
    "log_analysis",
    "knowledge_query",
    "general_chat",
]

# 意图识别路径：结构化输出、文本降级、默认兜底
IntentResolution = Literal[
    "structured",
    "text_fallback",
    "default_fallback",
]

# 意图表达式：单个意图直接是类型名，多个领域用 | 连接，如 database_query|log_analysis
IntentExpression = str


class IntentConstants:
    """意图路由相关常量"""

    # ===== 意图白名单与兜底 =====

    SUPPORTED_TYPES: tuple[IntentType, ...] = get_args(IntentType)
    """支持的意图白名单，唯一来源是模块级 IntentType"""

    DEFAULT: IntentType = "article_search"
    """无法识别意图时的兜底意图，权限最低且可公开访问"""

    GENERAL_CHAT: IntentType = "general_chat"
    """闲聊意图，只有单独出现时才走直连对话"""

    RESTRICTED: tuple[IntentType, ...] = ("database_query", "log_analysis")
    """受限意图，需要登录并逐项做工具权限校验"""

    # ===== 关键词与结构化字段 =====

    MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "database_query",
            ("database", "数据库", "sql", "表结构", "用户数据", "聊天记录"),
        ),
        (
            "article_search",
            (
                "article",
                "search",
                "文章",
                "教程",
                "技术知识",
                "搜索文章",
                "查找文章",
            ),
        ),
        (
            "log_analysis",
            ("log", "日志", "api调用", "接口调用", "错误日志", "异常日志"),
        ),
        (
            "knowledge_query",
            ("knowledge", "知识图谱", "图谱", "关联关系", "相似文章", "推荐"),
        ),
        (
            "general_chat",
            ("general", "chat", "闲聊"),
        ),
    )
    """意图关键词表，按优先级排列，键为意图类型，文本降级链路用它把模型输出映射为意图并补充多领域信号"""

    STRUCTURED_TYPES_DESCRIPTION: str = (
        "识别出的用户意图类型列表，可同时包含多个领域，"
        "只有纯闲聊且不需要调用任何工具（含 mcp_ 前缀的外部扩展工具）时才给出 general_chat"
    )
    """结构化输出中意图类型列表字段的说明文案"""
    STRUCTURED_CONFIDENCE_DESCRIPTION: str = "意图识别的置信度"
    """结构化输出中置信度字段的说明文案"""
