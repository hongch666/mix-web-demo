from functools import lru_cache
from typing import Any

from app.core.config import load_config
from app.internal.schemas.algorithmDTO import ScoreWeightItem


class AlgorithmService:
    """搜索算法权重服务 —— 所有排序公式权重的权威来源"""

    WEIGHT_DEFINITIONS: list[tuple[str, str, float, str]] = [
        # ── ES 传统8项权重 ──
        ("es_score_weight", "scoring.es_score_weight", 0.25, "ES BM25 相关度权重"),
        ("ai_rating_weight", "scoring.ai_rating_weight", 0.15, "AI 评分权重"),
        ("user_rating_weight", "scoring.user_rating_weight", 0.10, "用户评分权重"),
        ("views_weight", "scoring.views_weight", 0.08, "阅读量权重"),
        ("likes_weight", "scoring.likes_weight", 0.08, "点赞量权重"),
        ("collects_weight", "scoring.collects_weight", 0.08, "收藏量权重"),
        (
            "author_follow_weight",
            "scoring.author_follow_weight",
            0.04,
            "作者关注数权重",
        ),
        ("recency_weight", "scoring.recency_weight", 0.22, "新鲜度权重"),
        # ── 向量 ──
        ("vector_score_weight", "scoring.vector_score_weight", 0.25, "向量语义分权重"),
        # ── 图谱4路 ──
        (
            "graph_interest_weight",
            "scoring.graph_interest_weight",
            0.07,
            "图谱兴趣标签权重",
        ),
        (
            "graph_follow_weight",
            "scoring.graph_follow_weight",
            0.05,
            "图谱关注作者权重",
        ),
        (
            "graph_subcat_weight",
            "scoring.graph_subcat_weight",
            0.04,
            "图谱同子分类权重",
        ),
        (
            "graph_keyword_weight",
            "scoring.graph_keyword_weight",
            0.04,
            "图谱关键词标签权重",
        ),
        # ── 归一化上限 ──
        (
            "max_views_normalized",
            "scoring.max_views_normalized",
            10000.0,
            "阅读量归一化上限",
        ),
        (
            "max_likes_normalized",
            "scoring.max_likes_normalized",
            5000.0,
            "点赞量归一化上限",
        ),
        (
            "max_collects_normalized",
            "scoring.max_collects_normalized",
            5000.0,
            "收藏量归一化上限",
        ),
        (
            "max_follows_normalized",
            "scoring.max_follows_normalized",
            5000.0,
            "关注数归一化上限",
        ),
        # ── 时间衰减 ──
        (
            "recency_decay_days",
            "scoring.recency_decay_days",
            30.0,
            "新鲜度衰减参数(天)",
        ),
    ]

    def get_weights(self) -> dict[str, Any]:
        weights: list[ScoreWeightItem] = []
        for key, config_path, default, desc in self.WEIGHT_DEFINITIONS:
            value = self._read_config(config_path, default)
            weights.append(
                ScoreWeightItem(
                    key=key,
                    value=value,
                    description=desc,
                )
            )
        return {"weights": weights}

    @staticmethod
    def _read_config(config_path: str, default: float) -> float:
        cfg: dict[str, Any] = load_config("search") or {}
        keys = config_path.split(".")
        current: Any = cfg
        for k in keys:
            if isinstance(current, dict):
                current = current.get(k, {})
            else:
                return default
        try:
            return round(float(current), 4)
        except (TypeError, ValueError):
            return default


@lru_cache
def get_algorithm_service() -> AlgorithmService:
    return AlgorithmService()
