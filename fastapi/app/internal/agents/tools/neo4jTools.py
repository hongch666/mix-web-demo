import json
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional

from app.core.base import Constants, Logger
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


INTENT_TO_CYPHER: Dict[str, str] = {
    "article_detail": """
        MATCH (a:Article {id: $id})
        OPTIONAL MATCH (a)-[:PUBLISHED_BY]->(u:User)
        OPTIONAL MATCH (a)-[:BELONGS_TO]->(s:SubCategory)
        OPTIONAL MATCH (s)-[:BELONGS_TO_CATEGORY]->(c:Category)
        OPTIONAL MATCH (a)-[:TAGGED_AS]->(t:Tag)
        RETURN a.id AS id, a.title AS title, a.views AS views,
               u.name AS author, s.name AS subCategory, c.name AS category,
               collect(DISTINCT t.name) AS tags
    """,
    "category_articles": """
        MATCH (s:SubCategory {name: $name})<-[:BELONGS_TO]-(a:Article)
        OPTIONAL MATCH (a)-[:PUBLISHED_BY]->(u:User)
        RETURN a.id AS id, a.title AS title, a.views AS views,
               a.createAt AS createAt, u.name AS author
        ORDER BY a.views DESC LIMIT $limit
    """,
    "user_articles": """
        MATCH (a:Article)-[:PUBLISHED_BY]->(u:User {name: $name})
        RETURN a.id AS id, a.title AS title, a.views AS views, a.createAt AS createAt
        ORDER BY a.createAt DESC LIMIT $limit
    """,
    "similar_articles_same_category": """
        MATCH (a:Article {id: $articleId})-[:BELONGS_TO]->(s:SubCategory)
        MATCH (other:Article)-[:BELONGS_TO]->(s)
        WHERE other.id <> a.id
        OPTIONAL MATCH (other)-[:PUBLISHED_BY]->(u:User)
        RETURN other.id AS id, other.title AS title, other.views AS views,
               u.name AS author
        ORDER BY other.views DESC LIMIT $limit
    """,
    "user_interest_chain": """
        MATCH (u:User {id: $userId})-[:FOLLOWS]->(:User)-[:LIKES]->(a:Article)
        OPTIONAL MATCH (a)-[:PUBLISHED_BY]->(author:User)
        RETURN a.id AS id, a.title AS title, a.views AS views, author.name AS author
        ORDER BY a.views DESC LIMIT $limit
    """,
    "top_viewed_articles": """
        MATCH (a:Article)
        RETURN a.id AS id, a.title AS title, a.views AS views
        ORDER BY a.views DESC LIMIT $limit
    """,
    "tag_graph": """
        MATCH (t:Tag)<-[:TAGGED_AS]-(a:Article)
        RETURN t.name AS tag, count(a) AS articleCount
        ORDER BY articleCount DESC LIMIT $limit
    """,
    "user_recommendation": """
        MATCH (u:User {id: $userId})-[:LIKES|COLLECTS]->(interest:Article)
        MATCH (interest)-[:TAGGED_AS]->(t:Tag)
        MATCH (a:Article)-[:TAGGED_AS]->(t)
        WHERE a.id <> interest.id
          AND NOT EXISTS { (u)-[:LIKES|COLLECTS]->(a) }
        OPTIONAL MATCH (a)-[:PUBLISHED_BY]->(author:User)
        RETURN a.id AS id, a.title AS title, author.name AS author,
               collect(DISTINCT t.name) AS matchTags,
               count(DISTINCT t) AS relevance
        ORDER BY relevance DESC, a.views DESC LIMIT $limit
    """,
}


class Neo4jQueryTools:
    """Neo4j 知识图谱查询工具集"""

    def __init__(self) -> None:
        self.logger = Logger
        self.client: Optional[Any] = None
        self._init_client()

    def _init_client(self) -> None:
        try:
            from app.core.db import get_neo4j_client

            self.client = get_neo4j_client()
            self.logger.info("Neo4j 查询工具初始化成功")
        except Exception as e:
            self.client = None
            self.logger.warning(f"Neo4j 查询工具初始化失败: {e}")

    @staticmethod
    def _normalize_limit(params: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(params)
        try:
            limit = int(normalized.get("limit", 10))
        except (TypeError, ValueError):
            limit = 10
        normalized["limit"] = max(1, min(limit, 50))
        return normalized

    async def execute_predefined_query(
        self, query_name: str, params: Optional[Dict[str, Any]] = None
    ) -> str:
        """执行预定义的知识图谱查询"""
        if self.client is None:
            return Constants.NEO4J_SERVICE_UNAVAILABLE_MESSAGE

        if query_name not in INTENT_TO_CYPHER:
            available = ", ".join(INTENT_TO_CYPHER.keys())
            return f"不支持的查询类型，可选: {available}"

        safe_params = self._normalize_limit(params or {})
        records = await self.client.run_query(INTENT_TO_CYPHER[query_name], safe_params)
        if not records:
            return "未找到相关知识图谱结果"

        result_lines = [f"查询 {query_name} 返回 {len(records)} 条结果:"]
        for index, record in enumerate(records, 1):
            fields = []
            for key, value in record.items():
                if isinstance(value, list):
                    fields.append(f"{key}: {', '.join(str(item) for item in value)}")
                elif value is not None:
                    fields.append(f"{key}: {value}")
            result_lines.append(f"{index}. {' | '.join(fields)}")
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
        blocked_keywords = (
            "CREATE",
            "MERGE",
            "SET",
            "DELETE",
            "DETACH",
            "REMOVE",
            "DROP",
            "LOAD CSV",
            "CALL APOC",
        )
        return not any(
            re.search(rf"\b{re.escape(keyword)}\b", normalized)
            for keyword in blocked_keywords
        )

    async def execute_custom_cypher(self, cypher_query: str) -> str:
        """执行自定义只读 Cypher 查询"""
        if self.client is None:
            return Constants.NEO4J_SERVICE_UNAVAILABLE_MESSAGE

        if not self._is_read_only_cypher(cypher_query):
            return Constants.NEO4J_READ_ONLY_LIMIT_MESSAGE

        records = await self.client.run_query(cypher_query)
        if not records:
            return "查询未返回结果"
        return json.dumps(records, ensure_ascii=False, indent=2, default=str)

    def get_langchain_tools(self) -> List[StructuredTool]:
        """获取 LangChain 工具对象"""

        class PredefinedQueryInput(BaseModel):
            query_name: str = Field(
                description="预定义查询名称，可选值: " + ", ".join(INTENT_TO_CYPHER)
            )
            params: Dict[str, Any] = Field(
                default_factory=dict,
                description='查询参数，例如 {"id": 1, "name": "人工智能", "limit": 10}',
            )

        class CustomCypherInput(BaseModel):
            cypher_query: str = Field(description="只读 Cypher 查询语句")

        return [
            StructuredTool(
                name=Constants.NEO4J_PREDEFINED_QUERY_TOOL_NAME,
                description=Constants.NEO4J_PREDEFINED_QUERY_TOOL_DESC,
                coroutine=self.execute_predefined_query,
                args_schema=PredefinedQueryInput,
            ),
            StructuredTool(
                name=Constants.NEO4J_CUSTOM_CYPHER_TOOL_NAME,
                description=Constants.NEO4J_CUSTOM_CYPHER_TOOL_DESC,
                coroutine=self.execute_custom_cypher,
                args_schema=CustomCypherInput,
            ),
        ]


@lru_cache
def get_neo4j_tools() -> Neo4jQueryTools:
    """获取 Neo4j 查询工具实例"""
    return Neo4jQueryTools()
