from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Dict, List

from app.core.base import Logger
from app.core.constants import Defaults, Messages
from app.core.db import get_neo4j_client
from app.internal.schemas.graphSearchDTO import (
    GraphRelationDTO,
    GraphSearchEnhanceItemDTO,
    GraphSearchEnhanceReq,
    GraphSearchEnhanceResp,
)


class GraphSearchService:
    """图谱搜索增强服务"""

    def __init__(
        self,
        tag_interest_weight: float = 0.35,
        followed_author_weight: float = 0.25,
        same_sub_category_weight: float = 0.20,
        candidate_similarity_weight: float = 0.20,
        keyword_tag_weight: float = 0.20,
    ) -> None:
        self.TAG_INTEREST_WEIGHT: float = tag_interest_weight
        self.FOLLOWED_AUTHOR_WEIGHT: float = followed_author_weight
        self.SAME_SUB_CATEGORY_WEIGHT: float = same_sub_category_weight
        self.CANDIDATE_SIMILARITY_WEIGHT: float = candidate_similarity_weight
        self.KEYWORD_TAG_WEIGHT: float = keyword_tag_weight

    async def enhance(self, req: GraphSearchEnhanceReq) -> GraphSearchEnhanceResp:
        """执行图谱增强, 返回候选文章的图谱分和推荐原因"""
        if not req.articleIds:
            return GraphSearchEnhanceResp()

        # 限制参数
        article_ids = req.articleIds[: min(req.limit, 50)]
        keyword = req.keyword[:100] if req.keyword else ""

        # 并行执行多个图谱信号查询
        tasks = []
        # 信号1: 用户兴趣标签 (需要 userId)
        if req.userId and req.userId > 0:
            tasks.append(self._query_tag_interest(req.userId, article_ids))
        else:
            tasks.append(self._empty_result(article_ids))

        # 信号2: 关注作者 (需要 userId)
        if req.userId and req.userId > 0:
            tasks.append(self._query_followed_author(req.userId, article_ids))
        else:
            tasks.append(self._empty_result(article_ids))

        # 信号3: 同子分类 (需要 userId)
        if req.userId and req.userId > 0:
            tasks.append(self._query_same_sub_category(req.userId, article_ids))
        else:
            tasks.append(self._empty_result(article_ids))

        # 信号4: 候选间相似标签
        tasks.append(self._query_candidate_similarity(article_ids))

        # 信号5: 关键词标签命中
        tasks.append(self._query_keyword_tag(article_ids, keyword))

        # 等待所有查询完成 (单个失败不影响其他)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 解析结果
        signal_results: List[Dict[int, dict]] = []
        for r in results:
            if isinstance(r, Exception):
                Logger.warning(Messages.GRAPH_SEARCH_QUERY_EXCEPTION_LOG.format(r))
                signal_results.append({})
            else:
                signal_results.append(r)

        # 合并分数
        article_scores: Dict[int, dict] = {}
        for article_id in article_ids:
            article_scores[article_id] = {
                "graphScore": 0.0,
                "relations": [],
                "matchedTags": [],
                "matchedPaths": [],
            }

        # 累加各信号分数
        for signal_result in signal_results:
            for article_id, data in signal_result.items():
                if article_id in article_scores:
                    base = article_scores[article_id]
                    base["graphScore"] = min(
                        base["graphScore"] + data.get("score", 0.0), 1.0
                    )
                    base["relations"].extend(data.get("relations", []))
                    base["matchedTags"].extend(data.get("matchedTags", []))
                    base["matchedPaths"].extend(data.get("matchedPaths", []))

        # 生成最终结果
        items = []
        sorted_ids = sorted(
            article_scores.keys(),
            key=lambda aid: article_scores[aid]["graphScore"],
            reverse=True,
        )

        for article_id in sorted_ids:
            data = article_scores[article_id]
            final_score = min(data["graphScore"], 1.0)
            if final_score < 0:
                final_score = 0.0

            reason = self._generate_reason(data["relations"])
            items.append(
                GraphSearchEnhanceItemDTO(
                    articleId=article_id,
                    graphScore=round(final_score, 4),
                    reason=reason,
                    relations=data["relations"],
                    matchedTags=data["matchedTags"],
                    matchedPaths=data["matchedPaths"],
                )
            )

        return GraphSearchEnhanceResp(items=items)

    async def _empty_result(self, article_ids: List[int]) -> Dict[int, dict]:
        """空结果 (不依赖用户行为时使用)"""
        return {}

    async def _query_tag_interest(
        self, user_id: int, article_ids: List[int]
    ) -> Dict[int, dict]:
        """信号1: 用户兴趣标签"""
        rows = await self._safe_query(
            Messages.GRAPH_SEARCH_TAG_INTEREST_CYPHER,
            {
                "userId": user_id,
                "articleIds": article_ids,
            },
        )

        result: Dict[int, dict] = {}
        for row in rows:
            aid = row.get("articleId")
            if aid is None:
                continue
            raw = row.get("rawScore", 0) or 0
            score = min(raw / 5.0, 1.0) * self.TAG_INTEREST_WEIGHT
            tags = row.get("matchedTags", []) or []
            result[aid] = {
                "score": score,
                "relations": [
                    GraphRelationDTO(
                        type="tag_interest",
                        name=tag,
                        score=round(score, 4),
                        reason=Messages.GRAPH_SEARCH_REASON_INTEREST,
                    )
                    for tag in tags
                ],
                "matchedTags": tags,
                "matchedPaths": [Messages.GRAPH_SEARCH_PATH_INTEREST],
            }
        return result

    async def _query_followed_author(
        self, user_id: int, article_ids: List[int]
    ) -> Dict[int, dict]:
        """信号2: 关注作者"""
        rows = await self._safe_query(
            Messages.GRAPH_SEARCH_FOLLOWED_AUTHOR_CYPHER,
            {
                "userId": user_id,
                "articleIds": article_ids,
            },
        )

        result: Dict[int, dict] = {}
        for row in rows:
            aid = row.get("articleId")
            if aid is None:
                continue
            names = row.get("names", []) or []
            result[aid] = {
                "score": self.FOLLOWED_AUTHOR_WEIGHT,
                "relations": [
                    GraphRelationDTO(
                        type="followed_author",
                        name=name,
                        score=self.FOLLOWED_AUTHOR_WEIGHT,
                        reason=Messages.GRAPH_SEARCH_REASON_FOLLOWED,
                    )
                    for name in names
                ],
                "matchedTags": [],
                "matchedPaths": [Messages.GRAPH_SEARCH_PATH_FOLLOWED],
            }
        return result

    async def _query_same_sub_category(
        self, user_id: int, article_ids: List[int]
    ) -> Dict[int, dict]:
        """信号3: 同子分类"""
        rows = await self._safe_query(
            Messages.GRAPH_SEARCH_SAME_SUB_CATEGORY_CYPHER,
            {
                "userId": user_id,
                "articleIds": article_ids,
            },
        )

        result: Dict[int, dict] = {}
        for row in rows:
            aid = row.get("articleId")
            if aid is None:
                continue
            raw = row.get("rawScore", 0) or 0
            score = min(raw / 5.0, 1.0) * self.SAME_SUB_CATEGORY_WEIGHT
            names = row.get("names", []) or []
            result[aid] = {
                "score": score,
                "relations": [
                    GraphRelationDTO(
                        type="same_sub_category",
                        name=name,
                        score=round(score, 4),
                        reason=Messages.GRAPH_SEARCH_REASON_SUB_CATEGORY,
                    )
                    for name in names
                ],
                "matchedTags": [],
                "matchedPaths": [Messages.GRAPH_SEARCH_PATH_SUB_CATEGORY],
            }
        return result

    async def _query_candidate_similarity(
        self, article_ids: List[int]
    ) -> Dict[int, dict]:
        """信号4: 候选间相似标签"""
        rows = await self._safe_query(
            Messages.GRAPH_SEARCH_CANDIDATE_SIMILARITY_CYPHER,
            {
                "articleIds": article_ids,
            },
        )

        result: Dict[int, dict] = {}
        for row in rows:
            aid = row.get("articleId")
            if aid is None:
                continue
            raw = row.get("rawScore", 0) or 0
            score = min(raw / 3.0, 1.0) * self.CANDIDATE_SIMILARITY_WEIGHT
            names = row.get("names", []) or []
            result[aid] = {
                "score": score,
                "relations": [
                    GraphRelationDTO(
                        type="candidate_similarity",
                        name="候选共享标签",
                        score=round(score, 4),
                        reason=Messages.GRAPH_SEARCH_REASON_CANDIDATE,
                    )
                ],
                "matchedTags": names,
                "matchedPaths": [Messages.GRAPH_SEARCH_PATH_CANDIDATE],
            }
        return result

    async def _query_keyword_tag(
        self, article_ids: List[int], keyword: str
    ) -> Dict[int, dict]:
        """信号5: 关键词标签命中"""
        if not keyword:
            return {}

        rows = await self._safe_query(
            Messages.GRAPH_SEARCH_KEYWORD_TAG_CYPHER,
            {
                "articleIds": article_ids,
                "keyword": keyword,
            },
        )

        result: Dict[int, dict] = {}
        for row in rows:
            aid = row.get("articleId")
            if aid is None:
                continue
            raw = row.get("rawScore", 0) or 0
            score = min(raw / 2.0, 1.0) * self.KEYWORD_TAG_WEIGHT
            names = row.get("names", []) or []
            result[aid] = {
                "score": score,
                "relations": [
                    GraphRelationDTO(
                        type="keyword_tag",
                        name=name,
                        score=round(score, 4),
                        reason=Messages.GRAPH_SEARCH_REASON_KEYWORD,
                    )
                    for name in names
                ],
                "matchedTags": names,
                "matchedPaths": [Messages.GRAPH_SEARCH_PATH_KEYWORD],
            }
        return result

    async def _safe_query(self, cypher: str, params: dict) -> List[dict]:
        """安全执行 Neo4j 查询, 失败时返回空列表"""
        try:
            neo4j = get_neo4j_client()
            return await neo4j.run_query(cypher, params)
        except Exception as e:
            Logger.warning(Messages.GRAPH_SEARCH_NEO4J_EXCEPTION_LOG.format(e))
            return []

    def _generate_reason(self, relations: List[GraphRelationDTO]) -> str:
        """根据关系优先级生成推荐原因"""
        priority_map = {
            "followed_author": ("来自你关注的作者 {name}", 1),
            "tag_interest": ("与你最近点赞/收藏过的标签 {name} 相似", 2),
            "same_sub_category": ("属于你常看的分类 {name}", 3),
            "keyword_tag": ("命中图谱标签 {name}", 4),
            "candidate_similarity": (Messages.GRAPH_SEARCH_REASON_CANDIDATE, 5),
        }

        # 按优先级排序, 取最高优先级
        best = None
        best_priority = 999

        for rel in relations:
            if rel.type in priority_map:
                template, priority = priority_map[rel.type]
                if priority < best_priority:
                    best_priority = priority
                    best = (
                        template.format(name=rel.name)
                        if "{name}" in template
                        else template
                    )

        if best:
            return best

        # 兜底: 如果只有候选相似标签
        for rel in relations:
            if rel.type == "candidate_similarity":
                return Messages.GRAPH_SEARCH_REASON_CANDIDATE

        return ""


@lru_cache
def get_graph_search_service() -> GraphSearchService:
    """获取 GraphSearchService 单例"""
    return GraphSearchService(
        tag_interest_weight=Defaults.GRAPH_TAG_INTEREST_WEIGHT,
        followed_author_weight=Defaults.GRAPH_FOLLOWED_AUTHOR_WEIGHT,
        same_sub_category_weight=Defaults.GRAPH_SAME_SUB_CATEGORY_WEIGHT,
        candidate_similarity_weight=Defaults.GRAPH_CANDIDATE_SIMILARITY_WEIGHT,
        keyword_tag_weight=Defaults.GRAPH_KEYWORD_TAG_WEIGHT,
    )
