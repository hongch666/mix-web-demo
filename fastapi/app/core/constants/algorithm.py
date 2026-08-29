from typing import Tuple

from .defaults import Defaults


class AlgorithmConstants:
    """搜索排序算法相关常量。"""

    # 权重定义表：权重键、默认值、说明
    WEIGHT_DEFINITIONS: Tuple[tuple[str, float | int, str], ...] = (
        # ES 传统8项权重
        ("es_score_weight", Defaults.SEARCH_ES_SCORE_WEIGHT, "ES BM25 相关度权重"),
        ("ai_rating_weight", Defaults.SEARCH_AI_RATING_WEIGHT, "AI 评分权重"),
        ("user_rating_weight", Defaults.SEARCH_USER_RATING_WEIGHT, "用户评分权重"),
        ("views_weight", Defaults.SEARCH_VIEWS_WEIGHT, "阅读量权重"),
        ("likes_weight", Defaults.SEARCH_LIKES_WEIGHT, "点赞量权重"),
        ("collects_weight", Defaults.SEARCH_COLLECTS_WEIGHT, "收藏量权重"),
        (
            "author_follow_weight",
            Defaults.SEARCH_AUTHOR_FOLLOW_WEIGHT,
            "作者关注数权重",
        ),
        ("recency_weight", Defaults.SEARCH_RECENCY_WEIGHT, "新鲜度权重"),
        # 归一化上限
        (
            "max_views_normalized",
            Defaults.SEARCH_MAX_VIEWS_NORMALIZED,
            "阅读量归一化上限",
        ),
        (
            "max_likes_normalized",
            Defaults.SEARCH_MAX_LIKES_NORMALIZED,
            "点赞量归一化上限",
        ),
        (
            "max_collects_normalized",
            Defaults.SEARCH_MAX_COLLECTS_NORMALIZED,
            "收藏量归一化上限",
        ),
        (
            "max_follows_normalized",
            Defaults.SEARCH_MAX_FOLLOWS_NORMALIZED,
            "关注数归一化上限",
        ),
        # 时间衰减
        (
            "recency_decay_days",
            Defaults.SEARCH_RECENCY_DECAY_DAYS,
            "新鲜度衰减参数(天)",
        ),
        # 向量与图谱权重
        (
            "vector_score_weight",
            Defaults.SEARCH_VECTOR_SCORE_WEIGHT,
            "向量语义分融合权重",
        ),
        (
            "graph_score_weight",
            Defaults.SEARCH_GRAPH_SCORE_WEIGHT,
            "图谱增强分融合权重",
        ),
        (
            "hybrid_min_es_weight",
            Defaults.SEARCH_HYBRID_MIN_ES_WEIGHT,
            "融合时 ES 最低保底权重",
        ),
    )

    # 脚本参数映射表：权重键、脚本参数名、说明
    SCRIPT_PARAM_MAPPINGS: Tuple[tuple[str, str, str], ...] = (
        # ES 传统8项权重
        ("es_score_weight", "esWeight", "ES BM25 相关度权重"),
        ("ai_rating_weight", "aiWeight", "AI 评分权重"),
        ("user_rating_weight", "userWeight", "用户评分权重"),
        ("views_weight", "viewsWeight", "阅读量权重"),
        ("likes_weight", "likesWeight", "点赞量权重"),
        ("collects_weight", "collectsWeight", "收藏量权重"),
        ("author_follow_weight", "followWeight", "作者关注数权重"),
        ("recency_weight", "recencyWeight", "新鲜度权重"),
        # 归一化上限
        ("max_views_normalized", "maxViewsNormalized", "阅读量归一化上限"),
        ("max_likes_normalized", "maxLikesNormalized", "点赞量归一化上限"),
        ("max_collects_normalized", "maxCollectsNormalized", "收藏量归一化上限"),
        ("max_follows_normalized", "maxFollowsNormalized", "关注数归一化上限"),
        # 时间衰减
        ("recency_decay_days", "decayDaysSq", "新鲜度衰减参数(天)"),
    )
