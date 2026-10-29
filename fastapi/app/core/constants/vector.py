class VectorConstants:
    """向量库相关常量"""

    # ===== 向量库 =====

    COLLECTION_NAME: str = "articles"
    """文章向量统一写入的 collection"""

    # ===== 文本切分 =====

    CHUNK_SIZE: int = 800
    """单篇文章在向量库中的分块字符数"""
    CHUNK_OVERLAP: int = 100
    """相邻分块的重叠字符数，避免语义在切分处被切断"""
    CHUNK_SEPARATORS: list[str] = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    """分块时的分隔符优先级，按从粗到细排列"""

    # ===== Prompt 注入防御 =====

    INJECTION_PATTERNS: list[str] = [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
        r"you\s+are\s+(now\s+)?DAN",
        r"from\s+now\s+on\s+you\s+are",
        r"\[SYSTEM\]",
        r"output\s+(your|all)\s+(system\s+)?prompt",
        r"reveal\s+(your|the)\s+(instructions?|api.?key)",
        r"pretend\s+(you\s+are|to\s+be)",
        r"act\s+as\s+if\s+you\s+are",
    ]
    """Prompt 注入防御正则，入库前清洗文章内容，检索侧复用同一份规则"""
