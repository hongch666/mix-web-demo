import asyncio
import json
import re
from functools import lru_cache
from typing import Any, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.core.base import Logger
from app.core.constants import Messages, Prompts, Scripts
from app.core.db import get_neo4j_client
from app.internal.models import Article, User


class Neo4jQueryTools:
    """Neo4j 知识图谱查询工具集

    预定义查询分两类：
    - 能用 neomodel OGM 函数表达的查询，走 ``_ogm_handlers``（对象遍历 + traverse 预加载）；
    - 库内聚合统计、多跳集合并等 OGM 无法表达（或改写后需放弃库内 LIMIT、
      造成结果集放大）的查询，保留原始 Cypher
    """

    def __init__(self) -> None:
        self.logger = Logger
        self.client: Optional[Any] = None
        # query_name -> OGM 异步处理函数
        self._ogm_handlers: dict[str, Any] = {
            "article_detail": self._query_article_detail,
            "top_viewed_articles": self._query_top_viewed_articles,
            "user_articles": self._query_user_articles,
            "category_articles": self._query_category_articles,
            "similar_articles_same_category": self._query_similar_articles_same_category,
        }
        self._init_client()

    @property
    def available_query_names(self) -> list[str]:
        """全部预定义图谱查询名称（OGM 函数 + 原始 Cypher）"""
        return list(self._ogm_handlers) + list(Scripts.INTENT_TO_CYPHER)

    def _init_client(self) -> None:
        try:
            self.client = get_neo4j_client()
            self.logger.info(Messages.NEO4J_QUERY_TOOLS_INITIALIZED_MESSAGE)
        except Exception as e:
            self.client = None
            self.logger.warning(Messages.NEO4J_QUERY_TOOL_INITIALIZATION_FAILED(e))

    @staticmethod
    def _normalize_limit(params: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(params)
        try:
            limit = int(normalized.get("limit", 10))
        except (TypeError, ValueError):
            limit = 10
        normalized["limit"] = max(1, min(limit, 50))
        return normalized

    @staticmethod
    def _first_related(node: Any, relation: str) -> Optional[Any]:
        """读取 traverse/resolve_subgraph 预加载结果中的单个关联节点

        neomodel 把预加载的关系存放在节点的 ``_relations`` 上（值为节点列表）
        """
        related = getattr(node, "_relations", {}).get(relation)
        if isinstance(related, list):
            return related[0] if related else None
        return related

    @classmethod
    def _related_name(cls, node: Any, relation: str) -> Optional[str]:
        """读取预加载关联节点的 name 属性"""
        related = cls._first_related(node, relation)
        return getattr(related, "name", None) if related is not None else None

    async def _query_article_detail(
        self, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """文章详情：按 id 取文章并遍历作者、子分类、主分类与标签"""
        article_id = params.get("id")
        if article_id is None:
            return []

        try:
            article = await Article.nodes.get(graph_id=int(article_id))
        except Article.DoesNotExist:
            return []

        # 作者、子分类、标签相互独立，并行获取
        author, sub_category, tags = await asyncio.gather(
            article.author.single(),
            article.sub_category.single(),
            article.tags_rel.all(),
        )
        category = await sub_category.category.single() if sub_category else None

        return [
            {
                "id": article.graph_id,
                "title": article.title,
                "views": article.views,
                "author": author.name if author else None,
                "subCategory": sub_category.name if sub_category else None,
                "category": category.name if category else None,
                "tags": [tag.name for tag in tags],
            }
        ]

    async def _query_top_viewed_articles(
        self, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """浏览量最高的文章：库内排序 + LIMIT"""
        limit = int(params.get("limit", 10))
        ordered = Article.nodes.order_by("-views")
        # 异步版没有 __getitem__，用 get_item(slice) 设置 limit，LIMIT 仍下推到库内
        limited = await ordered.get_item(slice(0, limit))
        articles = await limited.all()
        return [
            {"id": article.graph_id, "title": article.title, "views": article.views}
            for article in articles
        ]

    async def _query_user_articles(
        self, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """某个用户名下发布的文章：遍历 User -[:PUBLISHED_BY]- Article"""
        name = params.get("name")
        if not name:
            return []
        limit = int(params.get("limit", 10))

        users = await User.nodes.filter(name=name).all()
        if not users:
            return []

        article_lists = await asyncio.gather(
            *[user.published_articles.all() for user in users]
        )

        seen: set[int] = set()
        results: list[dict[str, Any]] = []
        for articles in article_lists:
            for article in articles:
                if article.graph_id in seen:
                    continue
                seen.add(article.graph_id)
                results.append(
                    {
                        "id": article.graph_id,
                        "title": article.title,
                        "views": article.views,
                        "createAt": article.create_at,
                    }
                )
        results.sort(key=lambda item: item.get("createAt") or "", reverse=True)
        return results[:limit]

    async def _query_category_articles(
        self, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """某个子分类下的文章：库内按浏览量排序 + LIMIT，作者随遍历一并取回"""
        name = params.get("name")
        if not name:
            return []
        limit = int(params.get("limit", 10))

        node_set = Article.nodes.filter(sub_category__name=name).order_by("-views")
        limited = await node_set.get_item(slice(0, limit))
        # traverse 预加载作者：文章与作者一条查询取回，避免逐行查作者（N+1）
        rows = await limited.traverse("author").resolve_subgraph()
        return [
            {
                "id": row.graph_id,
                "title": row.title,
                "views": row.views,
                "createAt": row.create_at,
                "author": self._related_name(row, "author"),
            }
            for row in rows
        ]

    async def _query_similar_articles_same_category(
        self, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """同子分类的相似文章（排除自身）：库内按浏览量排序 + LIMIT"""
        article_id = params.get("articleId")
        if article_id is None:
            return []
        limit = int(params.get("limit", 10))
        source_id = int(article_id)

        source_rows = (
            await Article.nodes.filter(graph_id=source_id)
            .traverse("sub_category")
            .resolve_subgraph()
        )
        if not source_rows:
            return []
        sub_category = self._first_related(source_rows[0], "sub_category")
        if sub_category is None:
            return []

        node_set = Article.nodes.filter(
            sub_category__graph_id=sub_category.graph_id,
            graph_id__ne=source_id,
        ).order_by("-views")
        limited = await node_set.get_item(slice(0, limit))
        rows = await limited.traverse("author").resolve_subgraph()
        return [
            {
                "id": row.graph_id,
                "title": row.title,
                "views": row.views,
                "author": self._related_name(row, "author"),
            }
            for row in rows
        ]

    async def execute_predefined_query(
        self, query_name: str, params: Optional[dict[str, Any]] = None
    ) -> str:
        """执行预定义的知识图谱查询"""
        if self.client is None:
            return Messages.NEO4J_SERVICE_UNAVAILABLE_MESSAGE

        safe_params = self._normalize_limit(params or {})

        handler = self._ogm_handlers.get(query_name)
        if handler is not None:
            # 能用 OGM 函数表达的图谱查询走 neomodel 对象遍历，
            # 与原始 Cypher 路径一样先确保连接可用
            if not await self.client.connect():
                return Messages.NEO4J_SERVICE_UNAVAILABLE_MESSAGE
            try:
                records = await handler(safe_params)
            except Exception as e:
                self.logger.warning(Messages.NEO4J_OGM_QUERY_FAILED(query_name, e))
                records = []
        elif query_name in Scripts.INTENT_TO_CYPHER:
            # 聚合统计、多跳集合并等无法用 OGM 函数表达，保留原始 Cypher
            records = await self.client.run_query(
                Scripts.INTENT_TO_CYPHER[query_name], safe_params
            )
        else:
            available = ", ".join(self.available_query_names)
            return Messages.NEO4J_QUERY_TYPE_UNSUPPORTED(available)

        if not records:
            return Messages.NEO4J_NO_RESULT_MESSAGE

        result_lines = [Messages.NEO4J_QUERY_RESULT_HEADER(query_name, len(records))]
        for index, record in enumerate(records, 1):
            fields = []
            for key, value in record.items():
                if isinstance(value, list):
                    fields.append(
                        Messages.NEO4J_QUERY_FIELD(
                            key, ", ".join(str(item) for item in value)
                        )
                    )
                elif value is not None:
                    fields.append(Messages.NEO4J_QUERY_FIELD(key, str(value)))
            result_lines.append(
                Messages.NEO4J_QUERY_RESULT_ROW(index, " | ".join(fields))
            )
        return "\n".join(result_lines)

    @staticmethod
    def _is_read_only_cypher(cypher_query: str) -> bool:
        normalized = re.sub(r"\s+", " ", (cypher_query or "").strip()).upper()
        if not normalized:
            return False
        if ";" in normalized.rstrip(";"):
            return False
        allowed_prefixes = ("MATCH ", "OPTIONAL MATCH ", "WITH ", "CALL DB.", "RETURN ")
        if not normalized.startswith(allowed_prefixes):
            return False
        return not any(
            re.search(rf"\b{re.escape(keyword)}\b", normalized)
            for keyword in Messages.BLOCKED_KEYWORDS
        )

    async def execute_custom_cypher(self, cypher_query: str) -> str:
        """执行自定义只读 Cypher 查询"""
        if self.client is None:
            return Messages.NEO4J_SERVICE_UNAVAILABLE_MESSAGE

        if not self._is_read_only_cypher(cypher_query):
            return Messages.NEO4J_READ_ONLY_LIMIT_MESSAGE

        records = await self.client.run_query(cypher_query)
        if not records:
            return Messages.NEO4J_QUERY_EMPTY_MESSAGE
        return json.dumps(records, ensure_ascii=False, indent=2, default=str)

    def get_langchain_tools(self) -> list[StructuredTool]:
        """获取 LangChain 工具对象"""

        class PredefinedQueryInput(BaseModel):
            query_name: str = Field(
                description=Messages.NEO4J_QUERY_NAME_INPUT_DESC
                + ", ".join(self.available_query_names)
            )
            params: dict[str, Any] = Field(
                default_factory=dict,
                description=Messages.NEO4J_QUERY_PARAMS_INPUT_DESC,
            )

        class CustomCypherInput(BaseModel):
            cypher_query: str = Field(
                description=Messages.NEO4J_CUSTOM_CYPHER_INPUT_DESC
            )

        return [
            StructuredTool(
                name=Messages.NEO4J_PREDEFINED_QUERY_TOOL_NAME,
                description=Prompts.NEO4J_PREDEFINED_QUERY_TOOL_DESC,
                coroutine=self.execute_predefined_query,
                args_schema=PredefinedQueryInput,
            ),
            StructuredTool(
                name=Messages.NEO4J_CUSTOM_CYPHER_TOOL_NAME,
                description=Prompts.NEO4J_CUSTOM_CYPHER_TOOL_DESC,
                coroutine=self.execute_custom_cypher,
                args_schema=CustomCypherInput,
            ),
        ]


@lru_cache
def get_neo4j_tools() -> Neo4jQueryTools:
    """获取 Neo4j 查询工具实例"""
    return Neo4jQueryTools()
