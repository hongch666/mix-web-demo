from functools import lru_cache
from typing import Any, Dict, List

from app.core.constants import Defaults, Scripts
from app.internal.schemas.algorithmDTO import ScoreWeightItem


class AlgorithmService:
    """搜索排序权重服务 — 所有排序公式权重的权威来源"""

    # 权重定义表: (key, default_value, description)
    WEIGHT_DEFINITIONS: List[tuple] = [
        # ES 传统8项权重
        ("es_score_weight",       Defaults.SEARCH_ES_SCORE_WEIGHT,       "ES BM25 相关度权重"),
        ("ai_rating_weight",      Defaults.SEARCH_AI_RATING_WEIGHT,      "AI 评分权重"),
        ("user_rating_weight",    Defaults.SEARCH_USER_RATING_WEIGHT,    "用户评分权重"),
        ("views_weight",          Defaults.SEARCH_VIEWS_WEIGHT,          "阅读量权重"),
        ("likes_weight",          Defaults.SEARCH_LIKES_WEIGHT,          "点赞量权重"),
        ("collects_weight",       Defaults.SEARCH_COLLECTS_WEIGHT,       "收藏量权重"),
        ("author_follow_weight",  Defaults.SEARCH_AUTHOR_FOLLOW_WEIGHT,  "作者关注数权重"),
        ("recency_weight",        Defaults.SEARCH_RECENCY_WEIGHT,        "新鲜度权重"),
        # 归一化上限
        ("max_views_normalized",  Defaults.SEARCH_MAX_VIEWS_NORMALIZED,   "阅读量归一化上限"),
        ("max_likes_normalized",  Defaults.SEARCH_MAX_LIKES_NORMALIZED,   "点赞量归一化上限"),
        ("max_collects_normalized", Defaults.SEARCH_MAX_COLLECTS_NORMALIZED, "收藏量归一化上限"),
        ("max_follows_normalized", Defaults.SEARCH_MAX_FOLLOWS_NORMALIZED, "关注数归一化上限"),
        # 时间衰减
        ("recency_decay_days",    Defaults.SEARCH_RECENCY_DECAY_DAYS,    "新鲜度衰减参数(天)"),
        # 向量与图谱权重
        ("vector_score_weight",   Defaults.SEARCH_VECTOR_SCORE_WEIGHT,   "向量语义分融合权重"),
        ("graph_score_weight",    Defaults.SEARCH_GRAPH_SCORE_WEIGHT,    "图谱增强分融合权重"),
        ("hybrid_min_es_weight",  Defaults.SEARCH_HYBRID_MIN_ES_WEIGHT,  "融合时 ES 最低保底权重"),
    ]

    def get_weights(self) -> Dict[str, Any]:
        weights: List[ScoreWeightItem] = []
        for key, value, desc in self.WEIGHT_DEFINITIONS:
            weights.append(ScoreWeightItem(
                key=key,
                value=round(float(value), 4),
                description=desc,
            ))
        return {"weights": weights}

    def get_es_script(self) -> Dict[str, Any]:
        """获取 ES Painless 搜索脚本

        返回使用 params.xxx 占位符的脚本模板，由 GoZero 调用方在运行时通过
        elastic.NewScript(script).Param(name, value) 方式传入具体的权重值后使用。
        """
        return {"es_script": Scripts.ES_SEARCH_SCRIPT}


@lru_cache
def get_algorithm_service() -> AlgorithmService:
    return AlgorithmService()
