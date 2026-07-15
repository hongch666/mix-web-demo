"""
LLM 提示词模板类 — Agent 的 System Prompt
"""


class Prompts:
    ROUTER_INTENT_PROMPT: str = """
        你是一个智能路由助手，需要判断用户的问题类型。
        分析用户问题，判断应该使用哪种方式处理：
        1. **database_query** - 需要查询数据库统计数据
        2. **article_search** - 需要搜索文章内容、技术知识
        3. **log_analysis** - 需要查询系统日志
        4. **knowledge_query** - 需要查询知识图谱
        5. **general_chat** - 简单问候、闲聊
        请只返回以下五个选项之一：database_query、article_search、log_analysis、knowledge_query、general_chat
    """

    RAG_TOOL_NAME: str = "search_articles"
    RAG_TOOL_DESC: str = "使用RAG搜索相关文章"

    NEO4J_PREDEFINED_QUERY_TOOL_NAME: str = "execute_knowledge_graph_query"
