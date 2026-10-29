class Defaults:
    """
    配置默认值类 — TTL、权重、超时
    """

    # ===== 缓存 =====

    CACHE_L1_TTL: int = 300
    """本地一级缓存默认存活秒数"""
    CACHE_L2_TTL: int = 600
    """Redis 二级缓存默认存活秒数，需长于 L1"""

    # ===== 分布式锁 =====

    LOCK_DEFAULT_EXPIRE: int = 30
    """分布式锁默认过期秒数，避免任务异常退出后锁不释放"""

    # ===== 远程调用边界 =====

    MONGODB_QUERY_MAX_LIMIT: int = 50
    """NestJS /mongo-tools/query 的 limit 上界，需与 QueryMongoDto 的 @Max 一致"""
    MONGODB_AGGREGATE_MAX_DOCS: int = 100
    """NestJS /mongo-tools/aggregate 返回结果条数上限"""
    MONGODB_AGGREGATE_MAX_STAGES: int = 6
    """MongoDB 聚合管道的阶段数上限"""
    MONGODB_AGGREGATE_STAGES: tuple[str, ...] = (
        "$match",
        "$project",
        "$addFields",
        "$group",
        "$sort",
        "$limit",
        "$count",
        "$unwind",
    )
    """允许的聚合阶段白名单，需与 NestJS MongoTools.ALLOWED_AGGREGATE_STAGES 一致"""

    # ===== 权限 =====

    SYSTEM_USER_ID: int = -1
    """无登录用户时的系统调用身份，与内部令牌 userId=-1 的语义一致"""
    ROLE_ADMIN: str = "admin"
    """管理员角色标识"""
    ROLE_USER: str = "user"
    """普通用户角色标识"""

    # ===== 图谱搜索权重配置 =====

    GRAPH_TAG_INTEREST_WEIGHT: float = 0.35
    """图谱召回中用户标签兴趣的权重"""
    GRAPH_FOLLOWED_AUTHOR_WEIGHT: float = 0.25
    """图谱召回中已关注作者的权重"""
    GRAPH_SAME_SUB_CATEGORY_WEIGHT: float = 0.20
    """图谱召回中同一子分类的权重"""
    GRAPH_CANDIDATE_SIMILARITY_WEIGHT: float = 0.20
    """图谱召回中候选相似度的权重"""
    GRAPH_KEYWORD_TAG_WEIGHT: float = 0.20
    """图谱召回中关键词命中标签的权重"""
    GRAPH_SEARCH_CANDIDATE_LIMIT: int = 200
    """图谱召回候选上限，需不小于 GoZero 侧 SEARCH_GRAPH_CANDIDATE_LIMIT"""

    # ===== 向量搜索配置 =====

    VECTOR_SEARCH_ENABLED: bool = True
    """是否启用向量语义增强"""
    VECTOR_SEARCH_CANDIDATE_LIMIT: int = 200
    """向量召回候选上限，需不小于 GoZero 侧 SEARCH_VECTOR_CANDIDATE_LIMIT"""
    VECTOR_SEARCH_FETCH_MULTIPLIER: int = 4
    """向量检索时放大取回的倍数"""
    VECTOR_SEARCH_MAX_MATCHED_CHUNKS: int = 2
    """单篇文章最多返回的匹配片段数"""
    VECTOR_SEARCH_MIN_SCORE: float = 0.3
    """向量相似度下限，低于该值不计入语义分"""
    VECTOR_SEARCH_SCORE_MODE: str = "similarity"
    """向量检索评分模式，similarity 表示按余弦相似度计分"""

    # ===== 搜索权重=====

    SEARCH_ES_SCORE_WEIGHT: float = 0.25
    """ES BM25 相关度权重"""
    SEARCH_AI_RATING_WEIGHT: float = 0.15
    """AI 评分权重"""
    SEARCH_USER_RATING_WEIGHT: float = 0.10
    """用户评分权重"""
    SEARCH_VIEWS_WEIGHT: float = 0.08
    """阅读量权重"""
    SEARCH_LIKES_WEIGHT: float = 0.08
    """点赞量权重"""
    SEARCH_COLLECTS_WEIGHT: float = 0.08
    """收藏量权重"""
    SEARCH_AUTHOR_FOLLOW_WEIGHT: float = 0.04
    """作者关注数权重"""
    SEARCH_RECENCY_WEIGHT: float = 0.22
    """新鲜度权重"""
    SEARCH_VECTOR_SCORE_WEIGHT: float = 0.25
    """向量语义分融合权重"""
    SEARCH_GRAPH_SCORE_WEIGHT: float = 0.20
    """图谱增强分融合权重"""
    SEARCH_HYBRID_MIN_ES_WEIGHT: float = 0.55
    """融合排序时 ES 分的最低保底权重"""
    SEARCH_MAX_VIEWS_NORMALIZED: float = 10000.0
    """阅读量归一化上限"""
    SEARCH_MAX_LIKES_NORMALIZED: float = 1000.0
    """点赞量归一化上限"""
    SEARCH_MAX_COLLECTS_NORMALIZED: float = 1000.0
    """收藏量归一化上限"""
    SEARCH_MAX_FOLLOWS_NORMALIZED: float = 5000.0
    """关注数归一化上限"""
    SEARCH_RECENCY_DECAY_DAYS: int = 30
    """新鲜度衰减天数，控制时间权重的衰减速度"""

    # ===== 参考资料提取器 =====

    TEMP_PDF_PATH_TEMPLATE: str = "/tmp/temp_pdf_{}.pdf"
    """参考资料 PDF 临时文件路径模板"""
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
    """抓取外部参考资料时携带的请求头，模拟浏览器规避反爬"""

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
    """正文提取前剔除的噪音元素正则，覆盖注释、脚本、样式、导航与广告"""

    # ===== 流式对话协议 =====

    STREAM_TYPE_THINKING: str = "thinking"
    """内部流式生成器的思考中消息类型"""
    STREAM_TYPE_CONTENT: str = "content"
    """内部流式生成器的正文增量消息类型"""
    STREAM_TYPE_ERROR: str = "error"
    """内部流式生成器的错误消息类型"""
    STREAM_TYPE_DONE: str = "done"
    """内部流式生成器的结束消息类型"""
    STREAM_DONE_SENTINEL: str = "[DONE]"
    """OpenAI 兼容分片的结束哨兵"""
    STREAM_OPENAI_CHUNK_OBJECT: str = "chat.completion.chunk"
    """OpenAI 兼容分片的 object 字段取值"""
    STREAM_OPENAI_COMPLETION_ID_PREFIX: str = "chatcmpl-"
    """OpenAI 兼容分片的 completion id 前缀"""
    STREAM_OPENAI_ASSISTANT_ROLE: str = "assistant"
    """OpenAI 兼容分片中的助手角色名"""
    STREAM_OPENAI_FINISH_REASON_STOP: str = "stop"
    """OpenAI 兼容分片的正常结束原因"""

    # ===== 聊天上下文估算与裁剪参数 =====

    CHAT_CONTEXT_MESSAGE_OVERHEAD_TOKENS: int = 4
    """单条消息在对话模板中的固定 token 开销，覆盖角色标记与分隔符"""
    CHAT_CONTEXT_MIN_ROUND_TOKENS: int = 64
    """仅剩一轮对话时允许的最小 token 额度"""
    CHAT_CONTEXT_NON_CJK_CHARS_PER_TOKEN: int = 4
    """非 CJK 字符的 token 估算比例，按 4 字符 1 token 计"""
    CHAT_CONTEXT_TRUNCATED_SUFFIX: str = "..."
    """上下文裁剪后追加的标记，便于模型感知内容已截断"""
