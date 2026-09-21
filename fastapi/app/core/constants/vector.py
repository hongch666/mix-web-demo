class VectorConstants:
    """向量库相关常量"""

    # 文章向量统一写入的 collection
    COLLECTION_NAME: str = "articles"

    # 文本切分参数，决定单篇文章在向量库中的分块粒度
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100
    CHUNK_SEPARATORS: list[str] = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]

    # Prompt 注入防御模式，入库前清洗文章内容，检索侧复用同一份规则
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
