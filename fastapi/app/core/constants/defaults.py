class Defaults:
    """
    配置默认值类 — TTL、权重、超时
    """

    # ===== 缓存 =====
    CACHE_L1_TTL: int = 300
    CACHE_L2_TTL: int = 600

    # ===== 分布式锁 =====
    LOCK_DEFAULT_EXPIRE: int = 30

    # ===== 权限 =====
    ROLE_ADMIN: str = "admin"
    ROLE_USER: str = "user"

    # ===== 图谱搜索权重配置 =====
    GRAPH_TAG_INTEREST_WEIGHT: float = 0.35
    GRAPH_FOLLOWED_AUTHOR_WEIGHT: float = 0.25
    GRAPH_SAME_SUB_CATEGORY_WEIGHT: float = 0.20
    GRAPH_CANDIDATE_SIMILARITY_WEIGHT: float = 0.20
    GRAPH_KEYWORD_TAG_WEIGHT: float = 0.20

    # ===== 向量搜索配置 =====
    VECTOR_SEARCH_ENABLED: bool = True
    VECTOR_SEARCH_CANDIDATE_LIMIT: int = 50
    VECTOR_SEARCH_FETCH_MULTIPLIER: int = 4
    VECTOR_SEARCH_MAX_MATCHED_CHUNKS: int = 2
    VECTOR_SEARCH_MIN_SCORE: float = 0.3
    VECTOR_SEARCH_SCORE_MODE: str = "similarity"

    # ===== 权限关键词 =====
    PERSONAL_INFO_KEYWORDS: list = [
        "我的",
        "个人",
        "自己的",
        "本人的",
        "我",
        "自己",
        "点赞",
        "收藏",
        "喜欢",
        "评论",
        "互动",
        "关注",
    ]

    # ===== 搜索权重=====
    SEARCH_ES_SCORE_WEIGHT: float = 0.25
    SEARCH_AI_RATING_WEIGHT: float = 0.15
    SEARCH_USER_RATING_WEIGHT: float = 0.10
    SEARCH_VIEWS_WEIGHT: float = 0.08
    SEARCH_LIKES_WEIGHT: float = 0.08
    SEARCH_COLLECTS_WEIGHT: float = 0.08
    SEARCH_AUTHOR_FOLLOW_WEIGHT: float = 0.04
    SEARCH_RECENCY_WEIGHT: float = 0.22
    SEARCH_VECTOR_SCORE_WEIGHT: float = 0.25
    SEARCH_GRAPH_SCORE_WEIGHT: float = 0.20
    SEARCH_HYBRID_MIN_ES_WEIGHT: float = 0.55
    SEARCH_MAX_VIEWS_NORMALIZED: float = 10000.0
    SEARCH_MAX_LIKES_NORMALIZED: float = 1000.0
    SEARCH_MAX_COLLECTS_NORMALIZED: float = 1000.0
    SEARCH_MAX_FOLLOWS_NORMALIZED: float = 5000.0
    SEARCH_RECENCY_DECAY_DAYS: int = 30

    # ===== 参考资料提取器 =====
    TEMP_PDF_PATH_TEMPLATE: str = "/tmp/temp_pdf_{}.pdf"
    EXTRACTOR_REQUEST_HEADERS: dict = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    # 噪音元素过滤正则（HTML 注释、脚本、样式、导航、广告、版权标记等）
    EXTRACTOR_NOISE_PATTERNS: list[str] = [
        r"<!--.*?-->",
        r"<script.*?</script>",
        r"<style.*?</style>",
        r"<nav.*?</nav>",
        r"<footer.*?</footer>",
        r"<header.*?</header>",
        r"<aside.*?</aside>",
        r"<advertisement.*?</advertisement>",
        r'class=".*?ad.*?"[^>]*>.*?</[^>]*>',
        r'class=".*?nav.*?"[^>]*>.*?</[^>]*>',
        r'class=".*?sidebar.*?"[^>]*>.*?</[^>]*>',
        r'id=".*?ad.*?"[^>]*>.*?</[^>]*>',
        r"\s+(?:Click|Buy|Share|Like|Follow|Subscribe)\s+",
        r"(?:Advertisement|广告|赞助|推广):?",
        r"(?:Copyright|©|®|™)",
    ]
